"""
src/features.py

Feature engineering pour le projet :
Smart City Energy Forecasting — Tetouan.

Ce module transforme le dataset horaire propre en dataset supervisé pour le forecasting.

Il crée :
- features temporelles ;
- encodages cycliques sin/cos ;
- indicateurs week-end, heures de pointe, heures creuses ;
- saisons ;
- jours fériés marocains ;
- lag features ;
- rolling features sans data leakage ;
- HDD / CDD ;
- interactions météo ;
- variables utiles aux tests de robustesse.

Point important :
Les rolling features sont calculées avec shift(1), donc la valeur cible actuelle
n'entre jamais dans ses propres variables explicatives.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


DEFAULT_TARGET_COL = "target"
DEFAULT_TEMPERATURE_BASE = 18.0
DEFAULT_LAGS = (1, 2, 3, 6, 12, 24, 48, 72, 168)
DEFAULT_ROLLING_WINDOWS = (3, 6, 12, 24, 48, 168)


# Liste indicative pour 2017.
# Les jours religieux peuvent varier selon l'observation lunaire.
# Si un fichier externe data/external/holidays_morocco.csv est disponible,
# il est préférable de l'utiliser.
MOROCCO_HOLIDAYS_2017_INDICATIVE = pd.to_datetime(
    [
        "2017-01-01",  # Nouvel an
        "2017-01-11",  # Manifeste de l'indépendance
        "2017-05-01",  # Fête du travail
        "2017-06-26",  # Aïd al-Fitr - indicatif
        "2017-06-27",  # Aïd al-Fitr - indicatif
        "2017-07-30",  # Fête du Trône
        "2017-08-14",  # Allégeance Oued Eddahab
        "2017-08-20",  # Révolution du Roi et du Peuple
        "2017-08-21",  # Fête de la Jeunesse
        "2017-09-01",  # Aïd al-Adha - indicatif
        "2017-09-02",  # Aïd al-Adha - indicatif
        "2017-09-22",  # Nouvel an hégirien - indicatif
        "2017-11-06",  # Marche verte
        "2017-11-18",  # Fête de l'indépendance
        "2017-12-01",  # Aïd Al Mawlid - indicatif
    ]
)


@dataclass(frozen=True)
class FeatureConfig:
    """Configuration du pipeline de feature engineering."""

    target_col: str = DEFAULT_TARGET_COL
    temperature_col: str = "temperature"
    humidity_col: str = "humidity"
    general_diffuse_col: str = "general_diffuse_flows"
    diffuse_col: str = "diffuse_flows"

    temperature_base: float = DEFAULT_TEMPERATURE_BASE

    lags: Sequence[int] = DEFAULT_LAGS
    rolling_windows: Sequence[int] = DEFAULT_ROLLING_WINDOWS

    high_temperature_threshold: float = 30.0
    high_load_quantile: float = 0.95

    dropna_after_features: bool = True


def ensure_datetime_index(df: pd.DataFrame, datetime_col: str = "datetime") -> pd.DataFrame:
    """
    Garantit que le DataFrame possède un DatetimeIndex trié.

    Le DataFrame peut déjà avoir un DatetimeIndex ou contenir une colonne datetime.
    """
    out = df.copy()

    if isinstance(out.index, pd.DatetimeIndex):
        out = out.sort_index()
        return out

    if datetime_col not in out.columns:
        raise ValueError(
            f"Le DataFrame doit avoir un DatetimeIndex ou une colonne '{datetime_col}'."
        )

    out[datetime_col] = pd.to_datetime(out[datetime_col], errors="coerce")

    if out[datetime_col].isna().any():
        n_bad = int(out[datetime_col].isna().sum())
        raise ValueError(f"{n_bad} dates non convertibles détectées dans '{datetime_col}'.")

    out = out.sort_values(datetime_col).set_index(datetime_col)
    out.index.name = "datetime"

    return out


def validate_required_columns(df: pd.DataFrame, required_cols: Iterable[str]) -> None:
    """Vérifie que les colonnes nécessaires sont présentes."""
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError("Colonnes manquantes : " + ", ".join(missing))


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les variables temporelles calendaires.

    Ces variables représentent les cycles d'activité humaine par proxy :
    heure, jour de semaine, week-end, mois, saison, heures de pointe, etc.
    """
    out = ensure_datetime_index(df)

    out["hour"] = out.index.hour
    out["dayofweek"] = out.index.dayofweek  # 0 = lundi, 6 = dimanche
    out["dayofmonth"] = out.index.day
    out["dayofyear"] = out.index.dayofyear
    out["weekofyear"] = out.index.isocalendar().week.astype(int)
    out["month"] = out.index.month
    out["quarter"] = out.index.quarter

    out["is_weekend"] = (out["dayofweek"] >= 5).astype(int)

    out["is_business_hour"] = (
        (out["hour"].between(8, 18)) & (out["is_weekend"] == 0)
    ).astype(int)

    out["is_morning_peak"] = out["hour"].between(7, 9).astype(int)
    out["is_evening_peak"] = out["hour"].between(18, 21).astype(int)

    out["is_peak_hour"] = (
        (out["is_morning_peak"] == 1) | (out["is_evening_peak"] == 1)
    ).astype(int)

    out["is_off_peak"] = out["hour"].between(0, 5).astype(int)
    out["is_night"] = ((out["hour"] >= 23) | (out["hour"] <= 5)).astype(int)

    month_to_season = {
        12: "winter",
        1: "winter",
        2: "winter",
        3: "spring",
        4: "spring",
        5: "spring",
        6: "summer",
        7: "summer",
        8: "summer",
        9: "autumn",
        10: "autumn",
        11: "autumn",
    }

    season_to_code = {
        "winter": 0,
        "spring": 1,
        "summer": 2,
        "autumn": 3,
    }

    out["season"] = out["month"].map(month_to_season)
    out["season_code"] = out["season"].map(season_to_code).astype(int)

    season_dummies = pd.get_dummies(out["season"], prefix="season", dtype=int)
    out = pd.concat([out, season_dummies], axis=1)

    return out


def add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute l'encodage cyclique sin/cos.

    Objectif :
    éviter que le modèle considère 23h et 0h comme deux valeurs éloignées.
    """
    out = df.copy()

    validate_required_columns(out, ["hour", "dayofweek", "month", "dayofyear"])

    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24)

    out["dow_sin"] = np.sin(2 * np.pi * out["dayofweek"] / 7)
    out["dow_cos"] = np.cos(2 * np.pi * out["dayofweek"] / 7)

    out["month_sin"] = np.sin(2 * np.pi * (out["month"] - 1) / 12)
    out["month_cos"] = np.cos(2 * np.pi * (out["month"] - 1) / 12)

    out["doy_sin"] = np.sin(2 * np.pi * out["dayofyear"] / 365)
    out["doy_cos"] = np.cos(2 * np.pi * out["dayofyear"] / 365)

    return out


def load_holidays_from_csv(path: str | Path) -> pd.DatetimeIndex:
    """
    Charge les jours fériés depuis un CSV.

    Format recommandé :
    - une colonne appelée 'date'
    - ou une première colonne contenant les dates
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Fichier jours fériés introuvable : {path}")

    holidays = pd.read_csv(path)
    date_col = "date" if "date" in holidays.columns else holidays.columns[0]

    dates = pd.to_datetime(holidays[date_col], errors="coerce").dropna()
    dates = pd.DatetimeIndex(dates).normalize().unique()

    return dates


def add_holiday_features(
    df: pd.DataFrame,
    holidays: Iterable[pd.Timestamp] | None = None,
) -> pd.DataFrame:
    """Ajoute les indicateurs de jours fériés marocains."""
    out = ensure_datetime_index(df)

    if holidays is None:
        holiday_index = pd.DatetimeIndex(MOROCCO_HOLIDAYS_2017_INDICATIVE).normalize()
    else:
        holiday_index = pd.DatetimeIndex(pd.to_datetime(list(holidays))).normalize()

    normalized_dates = out.index.normalize()

    out["is_holiday"] = normalized_dates.isin(holiday_index).astype(int)

    out["is_day_before_holiday"] = (
        normalized_dates + pd.Timedelta(days=1)
    ).isin(holiday_index).astype(int)

    out["is_day_after_holiday"] = (
        normalized_dates - pd.Timedelta(days=1)
    ).isin(holiday_index).astype(int)

    if len(holiday_index) > 0:
        holiday_values = holiday_index.values.astype("datetime64[D]")
        current_values = normalized_dates.values.astype("datetime64[D]")

        distances = []

        for current_date in current_values:
            diff_days = np.abs(
                (holiday_values - current_date).astype("timedelta64[D]").astype(int)
            )
            distances.append(int(diff_days.min()))

        out["days_to_nearest_holiday"] = np.minimum(distances, 7)
    else:
        out["days_to_nearest_holiday"] = 7

    return out


def add_lag_features(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COL,
    lags: Sequence[int] = DEFAULT_LAGS,
) -> pd.DataFrame:
    """
    Ajoute les lags de la cible.

    Exemple :
    target_lag_24h = consommation de la même heure la veille.
    """
    out = df.copy()

    validate_required_columns(out, [target_col])

    for lag in lags:
        if lag <= 0:
            raise ValueError("Les lags doivent être strictement positifs.")

        out[f"{target_col}_lag_{lag}h"] = out[target_col].shift(lag)

    return out


def add_rolling_features(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COL,
    windows: Sequence[int] = DEFAULT_ROLLING_WINDOWS,
) -> pd.DataFrame:
    """
    Ajoute les statistiques glissantes de la cible.

    Anti-data leakage :
    on utilise target.shift(1), donc la ligne t utilise uniquement les valeurs
    disponibles jusqu'à t-1.
    """
    out = df.copy()

    validate_required_columns(out, [target_col])

    shifted_target = out[target_col].shift(1)

    for window in windows:
        if window <= 1:
            raise ValueError("Les fenêtres rolling doivent être supérieures à 1.")

        prefix = f"{target_col}_rolling_{window}h"
        rolling = shifted_target.rolling(window=window, min_periods=window)

        out[f"{prefix}_mean"] = rolling.mean()
        out[f"{prefix}_std"] = rolling.std(ddof=0)
        out[f"{prefix}_min"] = rolling.min()
        out[f"{prefix}_max"] = rolling.max()

    return out


def add_weather_features(
    df: pd.DataFrame,
    temperature_col: str = "temperature",
    humidity_col: str = "humidity",
    general_diffuse_col: str = "general_diffuse_flows",
    diffuse_col: str = "diffuse_flows",
    temperature_base: float = DEFAULT_TEMPERATURE_BASE,
) -> pd.DataFrame:
    """
    Ajoute les variables météorologiques dérivées.

    HDD :
    besoin théorique de chauffage.

    CDD :
    besoin théorique de climatisation.
    """
    out = df.copy()

    required = [
        temperature_col,
        humidity_col,
        general_diffuse_col,
        diffuse_col,
    ]
    validate_required_columns(out, required)

    out["HDD"] = np.maximum(temperature_base - out[temperature_col], 0)
    out["CDD"] = np.maximum(out[temperature_col] - temperature_base, 0)

    out["temperature_humidity_interaction"] = (
        out[temperature_col] * out[humidity_col]
    )

    if "is_peak_hour" in out.columns:
        out["temperature_peak_interaction"] = (
            out[temperature_col] * out["is_peak_hour"]
        )
        out["CDD_peak_interaction"] = out["CDD"] * out["is_peak_hour"]
        out["HDD_peak_interaction"] = out["HDD"] * out["is_peak_hour"]

    if "month" in out.columns:
        out["general_diffuse_month_interaction"] = (
            out[general_diffuse_col] * out["month"]
        )
        out["diffuse_month_interaction"] = out[diffuse_col] * out["month"]

    # Lags météo : l'effet thermique peut être retardé.
    for lag in (1, 2, 3, 6, 12):
        out[f"{temperature_col}_lag_{lag}h"] = out[temperature_col].shift(lag)
        out[f"{humidity_col}_lag_{lag}h"] = out[humidity_col].shift(lag)
        out[f"HDD_lag_{lag}h"] = out["HDD"].shift(lag)
        out[f"CDD_lag_{lag}h"] = out["CDD"].shift(lag)

    return out


def add_robustness_flags(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COL,
    high_temperature_threshold: float = 30.0,
    high_load_threshold: float | None = None,
) -> pd.DataFrame:
    """
    Ajoute des indicateurs utiles pour les tests de robustesse.

    Attention :
    eval_is_high_load est dérivée de la cible.
    Elle sert uniquement à découper l'évaluation.
    Elle ne doit pas être utilisée comme feature modèle.
    """
    out = df.copy()

    validate_required_columns(out, [target_col, "temperature"])

    out["is_high_temperature"] = (
        out["temperature"] >= high_temperature_threshold
    ).astype(int)

    # Variable prévue pour les scénarios de robustesse.
    out["is_heatwave_simulated"] = 0

    if high_load_threshold is not None:
        out["eval_is_high_load"] = (
            out[target_col] >= high_load_threshold
        ).astype(int)
    else:
        out["eval_is_high_load"] = 0

    return out


def build_feature_dataset(
    df: pd.DataFrame,
    config: FeatureConfig | None = None,
    holidays: Iterable[pd.Timestamp] | None = None,
    high_load_threshold: float | None = None,
) -> pd.DataFrame:
    """
    Pipeline complet de feature engineering.

    Le modèle prédit target(t) à partir :
    - des variables calendaires et météo à t ;
    - des lags de target avant t ;
    - des rolling statistics calculées uniquement avant t.
    """
    cfg = config or FeatureConfig()

    out = ensure_datetime_index(df)

    validate_required_columns(
        out,
        [
            cfg.target_col,
            cfg.temperature_col,
            cfg.humidity_col,
            cfg.general_diffuse_col,
            cfg.diffuse_col,
        ],
    )

    out = add_temporal_features(out)
    out = add_cyclical_features(out)
    out = add_holiday_features(out, holidays=holidays)

    out = add_lag_features(
        out,
        target_col=cfg.target_col,
        lags=cfg.lags,
    )

    out = add_rolling_features(
        out,
        target_col=cfg.target_col,
        windows=cfg.rolling_windows,
    )

    out = add_weather_features(
        out,
        temperature_col=cfg.temperature_col,
        humidity_col=cfg.humidity_col,
        general_diffuse_col=cfg.general_diffuse_col,
        diffuse_col=cfg.diffuse_col,
        temperature_base=cfg.temperature_base,
    )

    out = add_robustness_flags(
        out,
        target_col=cfg.target_col,
        high_temperature_threshold=cfg.high_temperature_threshold,
        high_load_threshold=high_load_threshold,
    )

    out = out.replace([np.inf, -np.inf], np.nan)

    if cfg.dropna_after_features:
        before = len(out)
        out = out.dropna().copy()
        out.attrs["rows_dropped_after_features"] = before - len(out)

    return out


def get_model_feature_columns(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COL,
    exclude_zone_loads: bool = True,
) -> list[str]:
    """
    Retourne les colonnes numériques utilisables comme variables explicatives.

    Colonnes exclues :
    - cible ;
    - consommations directes ;
    - total_load ;
    - variables d'évaluation ou de diagnostic dérivées de la cible ;
    - variables non disponibles au moment de la prédiction.
    """
    excluded = {
        target_col,
        "target",
        "zone1_power",
        "zone2_power",
        "zone3_power",
        "total_load",
        "season",

        # Colonnes de diagnostic issues du prétraitement.
        # Elles ne doivent pas être utilisées comme features modèle.
        "target_rolling_zscore",
        "total_load_rolling_zscore",
        "is_target_outlier",
        "is_total_load_outlier",
        "is_load_outlier",

        # Colonnes réservées à l'évaluation / robustesse.
        "eval_is_high_load",
        "is_heatwave_simulated",
    }

    if not exclude_zone_loads:
        excluded -= {"zone2_power", "zone3_power", "total_load"}

    numeric_cols = df.select_dtypes(include=[np.number, "bool"]).columns.tolist()

    feature_cols = [col for col in numeric_cols if col not in excluded]

    return feature_cols


def validate_feature_dataset(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COL,
    feature_cols: Sequence[str] | None = None,
) -> dict:
    """
    Vérifie la validité du dataset final de features.

    Contrôles :
    - DatetimeIndex ;
    - ordre chronologique ;
    - absence de doublons ;
    - présence de la cible ;
    - absence de NaN ;
    - absence de valeurs infinies.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Le dataset de features doit avoir un DatetimeIndex.")

    if not df.index.is_monotonic_increasing:
        raise ValueError("L'index temporel doit être trié dans l'ordre chronologique.")

    if df.index.has_duplicates:
        raise ValueError("Doublons temporels détectés dans le dataset de features.")

    if target_col not in df.columns:
        raise ValueError(f"Colonne cible absente : {target_col}")

    cols_to_check = list(feature_cols) if feature_cols is not None else df.columns.tolist()

    missing_values = df[cols_to_check].isna().sum()
    n_missing = int(missing_values.sum())

    if n_missing > 0:
        raise ValueError(f"{n_missing} valeurs manquantes détectées dans les features.")

    numeric = df[cols_to_check].select_dtypes(include=[np.number])
    n_infinite = int(np.isinf(numeric.to_numpy()).sum())

    if n_infinite > 0:
        raise ValueError(f"{n_infinite} valeurs infinies détectées dans les features.")

    report = {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "start": str(df.index.min()),
        "end": str(df.index.max()),
        "target_col": target_col,
        "n_model_features": int(len(feature_cols)) if feature_cols is not None else None,
        "n_missing": n_missing,
        "n_infinite": n_infinite,
        "inferred_frequency": pd.infer_freq(df.index),
    }

    return report


def check_rolling_no_leakage(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COL,
    windows: Sequence[int] = (3, 6, 24),
    atol: float = 1e-8,
) -> dict:
    """
    Vérifie que les rolling means sont bien calculées avec les valeurs passées.

    La formule attendue est :
    target.shift(1).rolling(window).mean()
    """
    report: dict[str, bool] = {}

    for window in windows:
        col = f"{target_col}_rolling_{window}h_mean"

        if col not in df.columns:
            continue

        expected = (
            df[target_col]
            .shift(1)
            .rolling(window=window, min_periods=window)
            .mean()
        )

        aligned = pd.concat([df[col], expected], axis=1).dropna()

        if aligned.empty:
            report[col] = False
        else:
            report[col] = bool(
                np.allclose(
                    aligned.iloc[:, 0],
                    aligned.iloc[:, 1],
                    atol=atol,
                )
            )

    return report


def save_feature_dataset(df: pd.DataFrame, path: str | Path) -> Path:
    """Sauvegarde le dataset enrichi en CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(path, index=True)

    return path