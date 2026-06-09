"""
src/models_ml.py
================

Module Machine Learning tabulaire pour le projet :
Smart City Energy Forecasting — Tetouan.

Objectif :
- entraîner Random Forest et XGBoost sur le dataset enrichi par feature engineering ;
- respecter la logique temporelle : aucun shuffle, split chronologique ;
- éviter le data leakage ;
- calculer les métriques globales et métier ;
- sauvegarder modèles, métriques, prédictions et importances.

Modèles :
- RandomForestRegressor : baseline ML robuste ;
- XGBRegressor : modèle ML principal performant sur les lags, rolling features,
  variables météo et variables calendaires.

Dépendances :
pip install pandas numpy scikit-learn matplotlib joblib xgboost
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Any
import json
import warnings

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance


# =============================================================================
# 1. Configurations
# =============================================================================

@dataclass(frozen=True)
class RandomForestConfig:
    """Configuration du modèle Random Forest."""

    n_estimators: int = 400
    max_depth: Optional[int] = None
    min_samples_leaf: int = 2
    min_samples_split: int = 2
    max_features: str = "sqrt"
    random_state: int = 42
    n_jobs: int = -1


@dataclass(frozen=True)
class XGBoostConfig:
    """Configuration du modèle XGBoost."""

    n_estimators: int = 1200
    learning_rate: float = 0.03
    max_depth: int = 5
    min_child_weight: float = 3.0
    subsample: float = 0.90
    colsample_bytree: float = 0.90
    reg_alpha: float = 0.05
    reg_lambda: float = 1.00
    objective: str = "reg:squarederror"
    eval_metric: str = "rmse"
    random_state: int = 42
    n_jobs: int = -1
    tree_method: str = "hist"


@dataclass(frozen=True)
class TemporalSplitConfig:
    """Configuration du split temporel train / validation / test."""

    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15

    def validate(self) -> None:
        total = self.train_ratio + self.val_ratio + self.test_ratio

        if not np.isclose(total, 1.0):
            raise ValueError(
                f"Les ratios doivent sommer à 1. Somme actuelle : {total:.4f}"
            )

        if min(self.train_ratio, self.val_ratio, self.test_ratio) <= 0:
            raise ValueError("Les trois ratios doivent être strictement positifs.")


# Colonnes à exclure pour éviter le data leakage.
DEFAULT_FORBIDDEN_FEATURES = {
    "target",
    "zone1_power",
    "zone2_power",
    "zone3_power",
    "total_load",
    "y",
    "prediction",
    "pred",
    "actual",
    "residual",
    "error",
    "absolute_error",
    "absolute_percentage_error",
    "split",
    "fold",
    "model",
}


# =============================================================================
# 2. Fonctions utilitaires
# =============================================================================

def set_global_seed(seed: int = 42) -> None:
    """Fixe la seed NumPy pour la reproductibilité."""

    np.random.seed(seed)


def ensure_datetime_index(
    df: pd.DataFrame,
    datetime_col: str = "datetime",
) -> pd.DataFrame:
    """
    Garantit que le DataFrame possède un DatetimeIndex trié.

    La fonction accepte plusieurs noms possibles :
    - datetime
    - DateTime
    - timestamp
    - date
    - Unnamed: 0

    Args:
        df: DataFrame source.
        datetime_col: nom préféré de la colonne temporelle.

    Returns:
        DataFrame avec DatetimeIndex.
    """

    out = df.copy()

    if isinstance(out.index, pd.DatetimeIndex):
        return out.sort_index()

    candidates = [
        datetime_col,
        "datetime",
        "DateTime",
        "timestamp",
        "Timestamp",
        "date",
        "Date",
        "Unnamed: 0",
    ]

    date_col = None
    for col in candidates:
        if col in out.columns:
            date_col = col
            break

    if date_col is None:
        raise ValueError(
            "Aucune colonne temporelle trouvée. Colonnes disponibles : "
            f"{list(out.columns)}"
        )

    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")

    if out[date_col].isna().any():
        n_bad = int(out[date_col].isna().sum())
        raise ValueError(f"{n_bad} dates non convertibles dans la colonne {date_col}.")

    out = out.set_index(date_col).sort_index()
    out.index.name = "datetime"

    return out


def resolve_target_column(
    df: pd.DataFrame,
    preferred: str = "target",
) -> str:
    """
    Détermine automatiquement la colonne cible.

    Priorité :
    1. preferred, par défaut target ;
    2. target ;
    3. zone1_power.

    Args:
        df: DataFrame.
        preferred: nom cible préféré.

    Returns:
        Nom de la colonne cible.
    """

    if preferred in df.columns:
        return preferred

    if "target" in df.columns:
        return "target"

    if "zone1_power" in df.columns:
        return "zone1_power"

    raise ValueError(
        "Aucune colonne cible trouvée. Attendu : target ou zone1_power. "
        f"Colonnes disponibles : {list(df.columns)}"
    )


def clean_numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Conserve uniquement les colonnes numériques et remplace inf/-inf par NaN.
    """

    out = df.select_dtypes(include=[np.number]).copy()
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def infer_feature_columns(
    df: pd.DataFrame,
    target_col: str,
    forbidden_features: Optional[Iterable[str]] = None,
    drop_current_zone_loads: bool = True,
) -> List[str]:
    """
    Déduit automatiquement les features numériques autorisées.

    Important :
    - on exclut target ;
    - on exclut zone1_power si target est une copie de zone1_power ;
    - on exclut les consommations courantes des autres zones par prudence ;
    - on garde les lags et rolling features, car ils représentent le passé.

    Args:
        df: DataFrame complet.
        target_col: colonne cible.
        forbidden_features: colonnes supplémentaires à exclure.
        drop_current_zone_loads: exclure les charges instantanées.

    Returns:
        Liste des colonnes features.
    """

    numeric_cols = clean_numeric_frame(df).columns.tolist()

    forbidden = {target_col}

    if drop_current_zone_loads:
        forbidden.update(DEFAULT_FORBIDDEN_FEATURES)

    if forbidden_features is not None:
        forbidden.update(forbidden_features)

    feature_cols = [c for c in numeric_cols if c not in forbidden]

    if len(feature_cols) == 0:
        raise ValueError("Aucune feature numérique disponible après exclusion.")

    return feature_cols


def prepare_supervised_data(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: Optional[Sequence[str]] = None,
    forbidden_features: Optional[Iterable[str]] = None,
    drop_current_zone_loads: bool = True,
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Prépare X et y pour les modèles ML.

    Étapes :
    - tri temporel ;
    - sélection des colonnes numériques ;
    - exclusion des colonnes de fuite ;
    - suppression des lignes contenant NaN dans X ou y.

    Args:
        df: DataFrame enrichi par feature engineering.
        target_col: colonne cible.
        feature_cols: liste optionnelle de features.
        forbidden_features: colonnes supplémentaires interdites.
        drop_current_zone_loads: exclure les charges courantes.

    Returns:
        X, y, feature_cols.
    """

    data = ensure_datetime_index(df)

    if target_col not in data.columns:
        raise ValueError(f"La cible {target_col} est absente du DataFrame.")

    if feature_cols is None:
        feature_cols = infer_feature_columns(
            data,
            target_col=target_col,
            forbidden_features=forbidden_features,
            drop_current_zone_loads=drop_current_zone_loads,
        )
    else:
        feature_cols = list(feature_cols)

    X = data[feature_cols].copy()
    y = data[target_col].copy()

    X = X.replace([np.inf, -np.inf], np.nan)
    y = y.replace([np.inf, -np.inf], np.nan)

    supervised = pd.concat([X, y.rename(target_col)], axis=1).dropna()

    X_clean = supervised[feature_cols]
    y_clean = supervised[target_col]

    return X_clean, y_clean, feature_cols


def temporal_train_val_test_split(
    X: pd.DataFrame,
    y: pd.Series,
    config: TemporalSplitConfig = TemporalSplitConfig(),
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Split chronologique train / validation / test.

    Aucun shuffle n'est utilisé.

    Args:
        X: features.
        y: cible.
        config: ratios du split.

    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test.
    """

    config.validate()

    if len(X) != len(y):
        raise ValueError("X et y doivent avoir la même longueur.")

    n = len(X)
    train_end = int(n * config.train_ratio)
    val_end = int(n * (config.train_ratio + config.val_ratio))

    X_train = X.iloc[:train_end].copy()
    X_val = X.iloc[train_end:val_end].copy()
    X_test = X.iloc[val_end:].copy()

    y_train = y.iloc[:train_end].copy()
    y_val = y.iloc[train_end:val_end].copy()
    y_test = y.iloc[val_end:].copy()

    return X_train, X_val, X_test, y_train, y_val, y_test


def print_split_summary(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    X_test: pd.DataFrame,
) -> None:
    """Affiche un résumé des splits temporels."""

    print("Résumé des splits temporels")
    print("-" * 60)
    print(f"Train : {X_train.index.min()} → {X_train.index.max()} | {len(X_train)} lignes")
    print(f"Val   : {X_val.index.min()} → {X_val.index.max()} | {len(X_val)} lignes")
    print(f"Test  : {X_test.index.min()} → {X_test.index.max()} | {len(X_test)} lignes")


# =============================================================================
# 3. Métriques
# =============================================================================

def safe_mape(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    epsilon: float = 1e-8,
) -> float:
    """
    Calcule le MAPE en évitant la division par zéro.

    Returns:
        MAPE en pourcentage.
    """

    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    denominator = np.maximum(np.abs(y_true_arr), epsilon)
    return float(np.mean(np.abs((y_true_arr - y_pred_arr) / denominator)) * 100)


def smape(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    epsilon: float = 1e-8,
) -> float:
    """
    Calcule le sMAPE.

    Returns:
        sMAPE en pourcentage.
    """

    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    denominator = np.maximum(np.abs(y_true_arr) + np.abs(y_pred_arr), epsilon)
    return float(200 * np.mean(np.abs(y_true_arr - y_pred_arr) / denominator))


def evaluate_regression(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    model_name: str,
) -> Dict[str, float]:
    """
    Calcule les métriques de régression.

    Métriques :
    - MAE ;
    - RMSE ;
    - MAPE ;
    - sMAPE ;
    - R² ;
    - biais moyen.

    Args:
        y_true: valeurs réelles.
        y_pred: prédictions.
        model_name: nom du modèle.

    Returns:
        Dictionnaire de métriques.
    """

    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    mae = mean_absolute_error(y_true_arr, y_pred_arr)
    rmse = np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))
    mape_value = safe_mape(y_true_arr, y_pred_arr)
    smape_value = smape(y_true_arr, y_pred_arr)
    r2 = r2_score(y_true_arr, y_pred_arr)
    bias = float(np.mean(y_pred_arr - y_true_arr))

    return {
        "model": model_name,
        "MAE": float(mae),
        "RMSE": float(rmse),
        "MAPE": float(mape_value),
        "sMAPE": float(smape_value),
        "R2": float(r2),
        "Bias": float(bias),
        "n_obs": int(len(y_true_arr)),
    }


def metrics_to_frame(metrics: Sequence[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convertit une liste de métriques en DataFrame trié par MAPE.
    """

    df = pd.DataFrame(metrics)

    if "MAPE" in df.columns:
        df = df.sort_values("MAPE", ascending=True).reset_index(drop=True)

    return df


# =============================================================================
# 4. Entraînement des modèles
# =============================================================================

def build_prediction_frame(
    y_true: pd.Series,
    y_pred: Sequence[float],
    model_name: str,
) -> pd.DataFrame:
    """
    Construit un DataFrame de prédictions aligné sur le temps.
    """

    out = pd.DataFrame(
        {
            "datetime": y_true.index,
            "actual": y_true.values,
            "prediction": np.asarray(y_pred, dtype=float),
        }
    )

    out["model"] = model_name
    out["residual"] = out["actual"] - out["prediction"]
    out["absolute_error"] = np.abs(out["residual"])
    out["absolute_percentage_error"] = (
        out["absolute_error"] / np.maximum(np.abs(out["actual"]), 1e-8) * 100
    )

    out["datetime"] = pd.to_datetime(out["datetime"])
    out["hour"] = out["datetime"].dt.hour
    out["dayofweek"] = out["datetime"].dt.dayofweek
    out["month"] = out["datetime"].dt.month

    return out


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    config: RandomForestConfig = RandomForestConfig(),
) -> RandomForestRegressor:
    """
    Entraîne un RandomForestRegressor.
    """

    model = RandomForestRegressor(**asdict(config))
    model.fit(X_train, y_train)

    return model


def train_evaluate_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    config: RandomForestConfig = RandomForestConfig(),
    model_name: str = "RandomForest",
) -> Tuple[RandomForestRegressor, Dict[str, float], pd.DataFrame]:
    """
    Entraîne Random Forest et évalue sur test.
    """

    model = train_random_forest(X_train, y_train, config=config)

    y_pred = model.predict(X_test)

    metrics = evaluate_regression(y_test, y_pred, model_name=model_name)
    pred_df = build_prediction_frame(y_test, y_pred, model_name=model_name)

    return model, metrics, pred_df


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: Optional[pd.DataFrame] = None,
    y_val: Optional[pd.Series] = None,
    config: XGBoostConfig = XGBoostConfig(),
    early_stopping_rounds: int = 50,
):
    """
    Entraîne un XGBRegressor.

    La fonction gère deux cas :
    - versions XGBoost acceptant early_stopping_rounds dans fit ;
    - versions XGBoost acceptant early_stopping_rounds dans le constructeur.
    """

    try:
        from xgboost import XGBRegressor
    except ImportError as exc:
        raise ImportError(
            "xgboost n'est pas installé. Installer avec : pip install xgboost"
        ) from exc

    params = asdict(config)

    eval_set = None
    if X_val is not None and y_val is not None:
        eval_set = [(X_val, y_val)]

    # Essai compatible avec XGBoost récent.
    try:
        model = XGBRegressor(
            **params,
            early_stopping_rounds=early_stopping_rounds if eval_set else None,
        )
        model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            verbose=False,
        )
        return model

    except TypeError:
        # Fallback compatible avec anciennes versions.
        model = XGBRegressor(**params)

        if eval_set is not None:
            model.fit(
                X_train,
                y_train,
                eval_set=eval_set,
                early_stopping_rounds=early_stopping_rounds,
                verbose=False,
            )
        else:
            model.fit(X_train, y_train)

        return model


def train_evaluate_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    config: XGBoostConfig = XGBoostConfig(),
    early_stopping_rounds: int = 50,
    model_name: str = "XGBoost",
):
    """
    Entraîne XGBoost et évalue sur test.
    """

    model = train_xgboost(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        config=config,
        early_stopping_rounds=early_stopping_rounds,
    )

    y_pred = model.predict(X_test)

    metrics = evaluate_regression(y_test, y_pred, model_name=model_name)
    pred_df = build_prediction_frame(y_test, y_pred, model_name=model_name)

    return model, metrics, pred_df


def predict_model(
    model,
    X: pd.DataFrame,
) -> np.ndarray:
    """
    Génère les prédictions d'un modèle scikit-learn compatible.
    """

    return np.asarray(model.predict(X), dtype=float)


# =============================================================================
# 5. Analyses métier
# =============================================================================

def evaluate_by_hour(pred_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les métriques par heure de la journée.

    Utile pour détecter une faiblesse pendant les heures de pointe.
    """

    rows = []

    for hour, group in pred_df.groupby("hour"):
        metrics = evaluate_regression(
            group["actual"],
            group["prediction"],
            model_name=str(group["model"].iloc[0]),
        )
        metrics["hour"] = int(hour)
        rows.append(metrics)

    out = pd.DataFrame(rows)
    cols = ["hour", "model", "MAE", "RMSE", "MAPE", "sMAPE", "R2", "Bias", "n_obs"]
    out = out[cols].sort_values("hour").reset_index(drop=True)

    return out


def evaluate_by_dayofweek(pred_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les métriques par jour de semaine.

    0 = lundi, 6 = dimanche.
    """

    day_map = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche",
    }

    rows = []

    for dow, group in pred_df.groupby("dayofweek"):
        metrics = evaluate_regression(
            group["actual"],
            group["prediction"],
            model_name=str(group["model"].iloc[0]),
        )
        metrics["dayofweek"] = int(dow)
        metrics["day_name"] = day_map.get(int(dow), str(dow))
        rows.append(metrics)

    out = pd.DataFrame(rows)
    cols = [
        "dayofweek",
        "day_name",
        "model",
        "MAE",
        "RMSE",
        "MAPE",
        "sMAPE",
        "R2",
        "Bias",
        "n_obs",
    ]
    out = out[cols].sort_values("dayofweek").reset_index(drop=True)

    return out


def evaluate_peak_load(
    pred_df: pd.DataFrame,
    quantile: float = 0.90,
) -> Dict[str, float]:
    """
    Évalue le modèle uniquement sur les fortes charges.

    Exemple :
    quantile=0.90 signifie qu'on garde les observations où actual est
    supérieur au 90e percentile du test.
    """

    threshold = pred_df["actual"].quantile(quantile)
    peak_df = pred_df[pred_df["actual"] >= threshold].copy()

    if peak_df.empty:
        raise ValueError("Aucune observation de forte charge trouvée.")

    model_name = str(pred_df["model"].iloc[0]) + f"_peak_q{quantile:.2f}"

    metrics = evaluate_regression(
        peak_df["actual"],
        peak_df["prediction"],
        model_name=model_name,
    )
    metrics["threshold"] = float(threshold)
    metrics["quantile"] = float(quantile)

    return metrics


# =============================================================================
# 6. Importance des variables
# =============================================================================

def feature_importance_table(
    model,
    feature_names: Sequence[str],
    top_n: Optional[int] = 30,
) -> pd.DataFrame:
    """
    Retourne l'importance native des variables.

    Compatible avec :
    - RandomForestRegressor : feature_importances_ ;
    - XGBRegressor : feature_importances_.
    """

    if not hasattr(model, "feature_importances_"):
        raise ValueError("Le modèle ne possède pas feature_importances_.")

    importances = np.asarray(model.feature_importances_, dtype=float)

    out = pd.DataFrame(
        {
            "feature": list(feature_names),
            "importance": importances,
        }
    ).sort_values("importance", ascending=False)

    out["rank"] = np.arange(1, len(out) + 1)

    if top_n is not None:
        out = out.head(top_n)

    return out.reset_index(drop=True)


def permutation_importance_table(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 5,
    random_state: int = 42,
    scoring: str = "neg_mean_absolute_error",
    top_n: Optional[int] = 30,
) -> pd.DataFrame:
    """
    Calcule l'importance par permutation.

    Plus une variable est importante, plus la performance baisse lorsqu'elle
    est mélangée.
    """

    result = permutation_importance(
        model,
        X,
        y,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring=scoring,
        n_jobs=-1,
    )

    out = pd.DataFrame(
        {
            "feature": X.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)

    out["rank"] = np.arange(1, len(out) + 1)

    if top_n is not None:
        out = out.head(top_n)

    return out.reset_index(drop=True)


# =============================================================================
# 7. Visualisations
# =============================================================================

def plot_actual_vs_predicted(
    pred_df: pd.DataFrame,
    title: str,
    path: Optional[Path] = None,
    max_points: Optional[int] = None,
):
    """
    Trace la série réelle vs prédite.

    Args:
        pred_df: DataFrame produit par build_prediction_frame.
        title: titre du graphique.
        path: chemin de sauvegarde optionnel.
        max_points: nombre de points à afficher, depuis la fin.
    """

    data = pred_df.copy()

    if max_points is not None and len(data) > max_points:
        data = data.tail(max_points)

    fig, ax = plt.subplots(figsize=(15, 5))

    ax.plot(data["datetime"], data["actual"], label="Réel", linewidth=1.3)
    ax.plot(data["datetime"], data["prediction"], label="Prédit", linewidth=1.3)

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Consommation")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150, bbox_inches="tight")

    return fig


def plot_feature_importance(
    importance_df: pd.DataFrame,
    title: str,
    path: Optional[Path] = None,
    top_n: int = 20,
):
    """
    Trace un barplot horizontal des importances de variables.
    """

    data = importance_df.head(top_n).copy()

    if "importance" in data.columns:
        value_col = "importance"
    elif "importance_mean" in data.columns:
        value_col = "importance_mean"
    else:
        raise ValueError("importance_df doit contenir importance ou importance_mean.")

    data = data.sort_values(value_col, ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.barh(data["feature"], data[value_col])
    ax.set_title(title)
    ax.set_xlabel("Importance")
    ax.set_ylabel("Variable")
    ax.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()

    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150, bbox_inches="tight")

    return fig


def plot_error_by_hour(
    hourly_metrics: pd.DataFrame,
    title: str,
    metric_col: str = "MAPE",
    path: Optional[Path] = None,
):
    """
    Trace une métrique d'erreur par heure.
    """

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(hourly_metrics["hour"], hourly_metrics[metric_col], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Heure")
    ax.set_ylabel(metric_col)
    ax.set_xticks(range(0, 24))
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150, bbox_inches="tight")

    return fig


# =============================================================================
# 8. Sauvegarde
# =============================================================================

def save_model(model, path: Path) -> None:
    """
    Sauvegarde un modèle avec joblib.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: Path):
    """
    Charge un modèle sauvegardé avec joblib.
    """

    return joblib.load(path)


def save_dataframe(
    df: pd.DataFrame,
    path: Path,
    index: bool = False,
) -> None:
    """
    Sauvegarde un DataFrame en CSV.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


def save_json(data: Dict[str, Any], path: Path) -> None:
    """
    Sauvegarde un dictionnaire en JSON.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_feature_names(
    feature_names: Sequence[str],
    path: Path,
) -> None:
    """
    Sauvegarde la liste des features utilisées par le modèle.
    """

    save_json({"feature_names": list(feature_names)}, path)