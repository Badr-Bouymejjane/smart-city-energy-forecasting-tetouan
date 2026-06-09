"""
src/models_sarima.py

Modèles SARIMA / SARIMAX pour le projet :
Smart City Energy Forecasting — Tetouan.

Objectif :
- entraîner un modèle SARIMA univarié sur la cible ;
- entraîner un modèle SARIMAX avec variables exogènes météo/calendaires ;
- produire des prédictions sur le test set ;
- calculer les métriques MAE, RMSE, MAPE, R2.

Remarque méthodologique :
SARIMAX avec exogènes suppose que les variables exogènes futures sont connues
ou prévisibles. Dans ce projet, on utilise les valeurs observées du test pour
évaluer le potentiel du modèle avec météo/calendrier disponibles.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.models_baseline import regression_metrics


@dataclass(frozen=True)
class SarimaConfig:
    """Configuration d'un modèle SARIMA ou SARIMAX."""

    model_name: str
    order: tuple[int, int, int] = (1, 0, 1)
    seasonal_order: tuple[int, int, int, int] = (1, 0, 1, 24)
    trend: str | None = "c"
    maxiter: int = 100
    max_train_size: int | None = 5000
    use_exog: bool = False
    scale_exog: bool = True


DEFAULT_SARIMAX_EXOG_COLS = [
    "temperature",
    "humidity",
    "wind_speed",
    "general_diffuse_flows",
    "diffuse_flows",
    "HDD",
    "CDD",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",
    "is_weekend",
    "is_holiday",
    "is_peak_hour",
    "is_off_peak",
]


def select_available_columns(
    df: pd.DataFrame,
    candidate_cols: Iterable[str],
) -> list[str]:
    """Retourne seulement les colonnes présentes dans le DataFrame."""
    return [col for col in candidate_cols if col in df.columns]


def prepare_sarimax_exog(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    exog_cols: Sequence[str],
    scale: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, StandardScaler | None]:
    """
    Prépare les variables exogènes pour SARIMAX.

    Le scaler est ajusté uniquement sur le train pour éviter le data leakage.
    """
    if not exog_cols:
        raise ValueError("La liste exog_cols est vide.")

    missing_train = [col for col in exog_cols if col not in train_df.columns]
    missing_test = [col for col in exog_cols if col not in test_df.columns]

    if missing_train or missing_test:
        raise ValueError(
            "Colonnes exogènes absentes. "
            f"Train: {missing_train}, Test: {missing_test}"
        )

    exog_train = train_df[list(exog_cols)].copy()
    exog_test = test_df[list(exog_cols)].copy()

    exog_train = exog_train.replace([np.inf, -np.inf], np.nan)
    exog_test = exog_test.replace([np.inf, -np.inf], np.nan)

    if exog_train.isna().sum().sum() > 0 or exog_test.isna().sum().sum() > 0:
        raise ValueError("Valeurs manquantes détectées dans les variables exogènes.")

    if not scale:
        return exog_train, exog_test, None

    scaler = StandardScaler()

    exog_train_scaled = pd.DataFrame(
        scaler.fit_transform(exog_train),
        index=exog_train.index,
        columns=exog_train.columns,
    )

    exog_test_scaled = pd.DataFrame(
        scaler.transform(exog_test),
        index=exog_test.index,
        columns=exog_test.columns,
    )

    return exog_train_scaled, exog_test_scaled, scaler


def _limit_train_size(
    train_df: pd.DataFrame,
    max_train_size: int | None,
) -> pd.DataFrame:
    """Limite la taille d'entraînement pour accélérer SARIMA/SARIMAX."""
    if max_train_size is None:
        return train_df.copy()

    if len(train_df) <= max_train_size:
        return train_df.copy()

    return train_df.iloc[-max_train_size:].copy()


def fit_sarimax_model(
    train_df: pd.DataFrame,
    target_col: str,
    config: SarimaConfig,
    exog_cols: Sequence[str] | None = None,
) -> tuple[object, pd.DataFrame | None, StandardScaler | None, pd.DataFrame]:
    """
    Entraîne un modèle SARIMA ou SARIMAX.

    Returns
    -------
    fitted_model:
        Résultat fitted de statsmodels.
    exog_train:
        Variables exogènes utilisées pour l'entraînement, ou None.
    scaler:
        Scaler ajusté sur exog_train, ou None.
    train_used:
        Partie train réellement utilisée.
    """
    train_used = _limit_train_size(train_df, config.max_train_size)

    y_train = train_used[target_col].astype(float)

    exog_train = None
    scaler = None

    if config.use_exog:
        if exog_cols is None or len(exog_cols) == 0:
            raise ValueError("config.use_exog=True mais aucune colonne exogène fournie.")

        exog_full = train_df[list(exog_cols)].copy()
        exog_train_raw = exog_full.loc[train_used.index]

        exog_train_raw = exog_train_raw.replace([np.inf, -np.inf], np.nan)

        if exog_train_raw.isna().sum().sum() > 0:
            raise ValueError("Valeurs manquantes dans exog_train_raw.")

        if config.scale_exog:
            scaler = StandardScaler()
            exog_train = pd.DataFrame(
                scaler.fit_transform(exog_train_raw),
                index=exog_train_raw.index,
                columns=exog_train_raw.columns,
            )
        else:
            exog_train = exog_train_raw

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        model = SARIMAX(
            endog=y_train,
            exog=exog_train,
            order=config.order,
            seasonal_order=config.seasonal_order,
            trend=config.trend,
            enforce_stationarity=False,
            enforce_invertibility=False,
            initialization="approximate_diffuse",
        )

        fitted_model = model.fit(
            disp=False,
            maxiter=config.maxiter,
        )

    return fitted_model, exog_train, scaler, train_used


def forecast_sarimax_model(
    fitted_model: object,
    test_df: pd.DataFrame,
    config: SarimaConfig,
    exog_cols: Sequence[str] | None = None,
    scaler: StandardScaler | None = None,
) -> pd.Series:
    """
    Prédit sur la période test avec un modèle SARIMA/SARIMAX entraîné.
    """
    steps = len(test_df)

    exog_test = None

    if config.use_exog:
        if exog_cols is None or len(exog_cols) == 0:
            raise ValueError("config.use_exog=True mais exog_cols est vide.")

        exog_test_raw = test_df[list(exog_cols)].copy()
        exog_test_raw = exog_test_raw.replace([np.inf, -np.inf], np.nan)

        if exog_test_raw.isna().sum().sum() > 0:
            raise ValueError("Valeurs manquantes dans exog_test_raw.")

        if scaler is not None:
            exog_test = pd.DataFrame(
                scaler.transform(exog_test_raw),
                index=exog_test_raw.index,
                columns=exog_test_raw.columns,
            )
        else:
            exog_test = exog_test_raw

    forecast_result = fitted_model.get_forecast(
        steps=steps,
        exog=exog_test,
    )

    y_pred = pd.Series(
        forecast_result.predicted_mean.values,
        index=test_df.index,
        name=config.model_name,
    )

    return y_pred


def run_sarima_experiment(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str,
    config: SarimaConfig,
    exog_cols: Sequence[str] | None = None,
) -> tuple[dict, pd.Series, object]:
    """
    Entraîne, prédit et évalue un modèle SARIMA/SARIMAX.
    """
    fitted_model, _, scaler, train_used = fit_sarimax_model(
        train_df=train_df,
        target_col=target_col,
        config=config,
        exog_cols=exog_cols,
    )

    y_pred = forecast_sarimax_model(
        fitted_model=fitted_model,
        test_df=test_df,
        config=config,
        exog_cols=exog_cols,
        scaler=scaler,
    )

    y_true = test_df[target_col].loc[y_pred.index]

    metrics = {
        "model": config.model_name,
        "model_family": "SARIMA/SARIMAX",
        "n_train_obs": int(len(train_used)),
        "n_test_obs": int(len(y_true)),
        "order": str(config.order),
        "seasonal_order": str(config.seasonal_order),
        "use_exog": bool(config.use_exog),
        "n_exog_cols": int(len(exog_cols)) if exog_cols is not None else 0,
    }

    metrics.update(regression_metrics(y_true, y_pred))

    return metrics, y_pred, fitted_model


def save_sarima_outputs(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics_path: str | Path,
    predictions_path: str | Path,
) -> tuple[Path, Path]:
    """Sauvegarde les métriques et prédictions SARIMA/SARIMAX."""
    metrics_path = Path(metrics_path)
    predictions_path = Path(predictions_path)

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(metrics_path, index=False)
    predictions.to_csv(predictions_path, index=True)

    return metrics_path, predictions_path