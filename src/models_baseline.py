"""
src/models_baseline.py

Baselines naïves pour le projet :
Smart City Energy Forecasting — Tetouan.

Objectif :
créer des références minimales de performance avant SARIMAX, Prophet,
Random Forest, XGBoost ou GRU.

Baselines :
- naive_previous_hour : prédit target(t-1)
- naive_previous_day  : prédit target(t-24)
- naive_previous_week : prédit target(t-168)
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


DEFAULT_BASELINE_LAGS = {
    "naive_previous_hour": 1,
    "naive_previous_day": 24,
    "naive_previous_week": 168,
}


def temporal_train_val_test_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Découpe chronologiquement un DataFrame en train / validation / test.

    Aucun shuffle n'est utilisé.
    """
    if not 0 < train_ratio < 1:
        raise ValueError("train_ratio doit être entre 0 et 1.")

    if not 0 < val_ratio < 1:
        raise ValueError("val_ratio doit être entre 0 et 1.")

    if train_ratio + val_ratio >= 1:
        raise ValueError("train_ratio + val_ratio doit être inférieur à 1.")

    ordered = df.sort_index().copy()

    n = len(ordered)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train = ordered.iloc[:train_end].copy()
    val = ordered.iloc[train_end:val_end].copy()
    test = ordered.iloc[val_end:].copy()

    return train, val, test


def safe_mape(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    epsilon: float = 1e-8,
) -> float:
    """
    Calcule le MAPE en évitant une division par zéro.

    Le résultat est exprimé en pourcentage.
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    denominator = np.maximum(np.abs(y_true_arr), epsilon)

    mape = np.mean(np.abs((y_true_arr - y_pred_arr) / denominator)) * 100

    return float(mape)


def regression_metrics(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> dict[str, float]:
    """
    Calcule les métriques de régression utilisées pour le forecasting.

    Métriques :
    - MAE ;
    - RMSE ;
    - MAPE ;
    - R2.
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    metrics = {
        "MAE": float(mean_absolute_error(y_true_arr, y_pred_arr)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))),
        "MAPE": safe_mape(y_true_arr, y_pred_arr),
        "R2": float(r2_score(y_true_arr, y_pred_arr)),
    }

    return metrics


def make_naive_forecasts(
    series: pd.Series,
    lags: Mapping[str, int] | None = None,
) -> pd.DataFrame:
    """
    Crée les prédictions naïves à partir de décalages temporels.

    Exemples :
    - lag 1   : heure précédente ;
    - lag 24  : même heure la veille ;
    - lag 168 : même heure la semaine précédente.
    """
    if lags is None:
        lags = DEFAULT_BASELINE_LAGS

    forecasts = pd.DataFrame(index=series.index)

    for name, lag in lags.items():
        if lag <= 0:
            raise ValueError("Les lags de baseline doivent être strictement positifs.")

        forecasts[name] = series.shift(lag)

    return forecasts


def evaluate_naive_baselines(
    df: pd.DataFrame,
    target_col: str = "target",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    lags: Mapping[str, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Évalue les baselines naïves sur le test set chronologique.

    Les prédictions sont calculées sur toute la série avec shift(lag),
    puis évaluées uniquement sur la période de test.

    C'est valide parce que les valeurs passées avant le test sont connues
    au moment de prédire les premières observations du test.
    """
    if target_col not in df.columns:
        raise ValueError(f"Colonne cible absente : {target_col}")

    ordered = df.sort_index().copy()

    _, _, test = temporal_train_val_test_split(
        ordered,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
    )

    forecasts = make_naive_forecasts(
        ordered[target_col],
        lags=lags,
    )

    predictions = pd.DataFrame(index=test.index)
    predictions["y_true"] = ordered.loc[test.index, target_col]

    metrics_rows = []

    for model_name in forecasts.columns:
        aligned = pd.concat(
            [
                predictions["y_true"],
                forecasts.loc[test.index, model_name],
            ],
            axis=1,
        ).dropna()

        aligned.columns = ["y_true", "y_pred"]

        if aligned.empty:
            continue

        predictions.loc[aligned.index, model_name] = aligned["y_pred"]

        row = {
            "model": model_name,
            "n_test_obs": int(len(aligned)),
        }

        row.update(
            regression_metrics(
                aligned["y_true"],
                aligned["y_pred"],
            )
        )

        metrics_rows.append(row)

    metrics = (
        pd.DataFrame(metrics_rows)
        .sort_values("MAPE")
        .reset_index(drop=True)
    )

    return metrics, predictions


def save_baseline_outputs(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics_path: str | Path,
    predictions_path: str | Path,
) -> tuple[Path, Path]:
    """Sauvegarde les métriques et les prédictions baseline."""
    metrics_path = Path(metrics_path)
    predictions_path = Path(predictions_path)

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(metrics_path, index=False)
    predictions.to_csv(predictions_path, index=True)

    return metrics_path, predictions_path