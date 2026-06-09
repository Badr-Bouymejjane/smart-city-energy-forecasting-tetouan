"""
src/models_prophet.py

Modèles Prophet pour le projet :
Smart City Energy Forecasting — Tetouan.

Objectif :
- préparer les données au format Prophet : ds, y ;
- ajouter des régresseurs météo/calendaires ;
- ajouter les jours fériés marocains si disponibles ;
- entraîner Prophet ;
- prédire sur la période test ;
- calculer les métriques MAE, RMSE, MAPE, R2.

Remarque :
La bibliothèque Prophet peut ne pas être installée par défaut.
Installation recommandée :
    pip install prophet
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from src.models_baseline import regression_metrics


@dataclass(frozen=True)
class ProphetConfig:
    """Configuration du modèle Prophet."""

    model_name: str = "prophet_weather_calendar"
    yearly_seasonality: bool | str = False
    weekly_seasonality: bool | str = True
    daily_seasonality: bool | str = True
    seasonality_mode: str = "additive"
    changepoint_prior_scale: float = 0.05
    seasonality_prior_scale: float = 10.0
    holidays_prior_scale: float = 10.0
    interval_width: float = 0.95


DEFAULT_PROPHET_REGRESSORS = [
    "temperature",
    "humidity",
    "wind_speed",
    "general_diffuse_flows",
    "diffuse_flows",
    "HDD",
    "CDD",
    "is_weekend",
    "is_holiday",
    "is_peak_hour",
    "is_off_peak",
]


def import_prophet_class():
    """
    Importe Prophet.

    Lève une erreur claire si Prophet n'est pas installé.
    """
    try:
        from prophet import Prophet
    except ImportError as exc:
        raise ImportError(
            "La bibliothèque Prophet n'est pas installée. "
            "Installe-la avec : pip install prophet"
        ) from exc

    return Prophet


def select_available_columns(
    df: pd.DataFrame,
    candidate_cols: Iterable[str],
) -> list[str]:
    """Retourne seulement les colonnes présentes dans le DataFrame."""
    return [col for col in candidate_cols if col in df.columns]


def prepare_prophet_dataframe(
    df: pd.DataFrame,
    target_col: str,
    regressor_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
    """
    Convertit un DataFrame temporel au format attendu par Prophet.

    Prophet attend :
    - ds : datetime ;
    - y : cible.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Le DataFrame doit avoir un DatetimeIndex.")

    if target_col not in df.columns:
        raise ValueError(f"Colonne cible absente : {target_col}")

    regressor_cols = list(regressor_cols or [])

    missing = [col for col in regressor_cols if col not in df.columns]

    if missing:
        raise ValueError("Régresseurs absents : " + ", ".join(missing))

    cols = [target_col] + regressor_cols

    prophet_df = df[cols].copy()
    prophet_df = prophet_df.replace([np.inf, -np.inf], np.nan)

    if prophet_df.isna().sum().sum() > 0:
        raise ValueError("Valeurs manquantes détectées dans les données Prophet.")

    prophet_df = prophet_df.reset_index()

    datetime_col = prophet_df.columns[0]

    prophet_df = prophet_df.rename(
        columns={
            datetime_col: "ds",
            target_col: "y",
        }
    )

    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)

    return prophet_df


def make_prophet_holidays(
    df: pd.DataFrame,
    holiday_col: str = "is_holiday",
    holiday_name: str = "morocco_holiday",
) -> pd.DataFrame | None:
    """
    Crée un DataFrame holidays pour Prophet à partir d'une colonne binaire is_holiday.

    Prophet applique l'effet au niveau de la date.
    """
    if holiday_col not in df.columns:
        return None

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Le DataFrame doit avoir un DatetimeIndex.")

    holiday_dates = (
        df.loc[df[holiday_col] == 1]
        .index.normalize()
        .unique()
    )

    if len(holiday_dates) == 0:
        return None

    holidays = pd.DataFrame(
        {
            "holiday": holiday_name,
            "ds": pd.to_datetime(holiday_dates),
            "lower_window": 0,
            "upper_window": 1,
        }
    )

    holidays["ds"] = holidays["ds"].dt.tz_localize(None)

    return holidays


def fit_prophet_model(
    train_df: pd.DataFrame,
    target_col: str,
    config: ProphetConfig,
    regressor_cols: Sequence[str] | None = None,
    holidays: pd.DataFrame | None = None,
):
    """
    Entraîne un modèle Prophet.
    """
    Prophet = import_prophet_class()

    regressor_cols = list(regressor_cols or [])

    prophet_train = prepare_prophet_dataframe(
        train_df,
        target_col=target_col,
        regressor_cols=regressor_cols,
    )

    model = Prophet(
        yearly_seasonality=config.yearly_seasonality,
        weekly_seasonality=config.weekly_seasonality,
        daily_seasonality=config.daily_seasonality,
        seasonality_mode=config.seasonality_mode,
        changepoint_prior_scale=config.changepoint_prior_scale,
        seasonality_prior_scale=config.seasonality_prior_scale,
        holidays_prior_scale=config.holidays_prior_scale,
        interval_width=config.interval_width,
        holidays=holidays,
    )

    for regressor in regressor_cols:
        model.add_regressor(regressor, standardize="auto")

    model.fit(prophet_train)

    return model


def forecast_prophet_model(
    model,
    df: pd.DataFrame,
    target_col: str,
    regressor_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
    """
    Produit les prédictions Prophet sur df.
    """
    regressor_cols = list(regressor_cols or [])

    prophet_future = prepare_prophet_dataframe(
        df,
        target_col=target_col,
        regressor_cols=regressor_cols,
    )

    future = prophet_future[["ds"] + regressor_cols].copy()

    forecast = model.predict(future)

    forecast = forecast.set_index(pd.to_datetime(forecast["ds"]))
    forecast.index.name = df.index.name

    return forecast


def run_prophet_experiment(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str,
    config: ProphetConfig,
    regressor_cols: Sequence[str] | None = None,
    holidays: pd.DataFrame | None = None,
) -> tuple[dict, pd.Series, pd.DataFrame, object]:
    """
    Entraîne, prédit et évalue Prophet.
    """
    regressor_cols = list(regressor_cols or [])

    model = fit_prophet_model(
        train_df=train_df,
        target_col=target_col,
        config=config,
        regressor_cols=regressor_cols,
        holidays=holidays,
    )

    forecast = forecast_prophet_model(
        model=model,
        df=test_df,
        target_col=target_col,
        regressor_cols=regressor_cols,
    )

    y_pred = pd.Series(
        forecast["yhat"].values,
        index=test_df.index,
        name=config.model_name,
    )

    y_true = test_df[target_col].loc[y_pred.index]

    metrics = {
        "model": config.model_name,
        "model_family": "Prophet",
        "n_train_obs": int(len(train_df)),
        "n_test_obs": int(len(test_df)),
        "yearly_seasonality": str(config.yearly_seasonality),
        "weekly_seasonality": str(config.weekly_seasonality),
        "daily_seasonality": str(config.daily_seasonality),
        "seasonality_mode": config.seasonality_mode,
        "n_regressors": int(len(regressor_cols)),
    }

    metrics.update(regression_metrics(y_true, y_pred))

    return metrics, y_pred, forecast, model


def save_prophet_outputs(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics_path: str | Path,
    predictions_path: str | Path,
) -> tuple[Path, Path]:
    """Sauvegarde les métriques et prédictions Prophet."""
    metrics_path = Path(metrics_path)
    predictions_path = Path(predictions_path)

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(metrics_path, index=False)
    predictions.to_csv(predictions_path, index=True)

    return metrics_path, predictions_path