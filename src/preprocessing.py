"""
src/preprocessing.py

Fonctions réutilisables pour le prétraitement du dataset Tetouan :
contrôle temporel, resampling horaire, valeurs manquantes, outliers,
split chronologique et normalisation sans data leakage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Literal, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler


BASE_WEATHER_FEATURES = [
    "temperature",
    "humidity",
    "wind_speed",
    "general_diffuse_flows",
    "diffuse_flows",
]

LOAD_COLUMNS = [
    "zone1_power",
    "zone2_power",
    "zone3_power",
    "target",
    "total_load",
]

FORBIDDEN_DIRECT_FEATURES = [
    "target",
    "zone1_power",
    "zone2_power",
    "zone3_power",
    "total_load",
    "target_rolling_zscore",
    "total_load_rolling_zscore",
    "is_target_outlier",
    "is_total_load_outlier",
    "is_load_outlier",
]


def ensure_datetime_index(df: pd.DataFrame) -> None:
    """
    Vérifie que le DataFrame possède un DatetimeIndex.

    Raises
    ------
    TypeError
        Si l'index n'est pas un DatetimeIndex.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Le DataFrame doit être indexé par un DatetimeIndex.")


def is_hourly_frequency(freq: str | None) -> bool:
    """
    Vérifie si une fréquence inférée correspond à un pas horaire.
    Compatible avec les notations pandas anciennes et récentes.
    """
    return str(freq) in {"h", "H", "1h", "1H"}


def check_10min_measurements_per_hour(
    df: pd.DataFrame,
    *,
    expected_per_hour: int = 6,
    raise_error: bool = True,
) -> pd.Series:
    """
    Vérifie que chaque heure brute contient exactement 6 mesures de 10 minutes.

    Cette vérification renforce la fiabilité du resampling horaire : une moyenne
    horaire doit être calculée sur le même nombre de mesures pour toutes les heures.

    Parameters
    ----------
    df:
        Dataset brut indexé à fréquence 10 minutes.
    expected_per_hour:
        Nombre attendu d'observations par heure.
    raise_error:
        Si True, lève une erreur si au moins une heure est incomplète.

    Returns
    -------
    pd.Series
        Série indexée par heure contenant le nombre de mesures par heure.
    """
    ensure_datetime_index(df)

    hourly_counts = df.resample("1h").size()
    incomplete_hours = hourly_counts[hourly_counts != expected_per_hour]

    if raise_error and len(incomplete_hours) > 0:
        raise ValueError(
            "Certaines heures ne contiennent pas exactement "
            f"{expected_per_hour} mesures. Nombre d'heures concernées : "
            f"{len(incomplete_hours)}"
        )

    return hourly_counts


def resample_hourly(
    df: pd.DataFrame,
    *,
    rule: str = "1h",
    check_counts: bool = True,
    expected_per_hour: int = 6,
) -> pd.DataFrame:
    """
    Rééchantillonne le dataset sur une grille horaire par moyenne.

    Parameters
    ----------
    df:
        Dataset brut indexé par datetime.
    rule:
        Fréquence cible, par défaut `1h`.
    check_counts:
        Si True, vérifie que chaque heure contient 6 mesures de 10 minutes.
    expected_per_hour:
        Nombre attendu de mesures par heure si `check_counts=True`.

    Returns
    -------
    pd.DataFrame
        Dataset horaire contenant uniquement les colonnes numériques.
    """
    ensure_datetime_index(df)

    if check_counts:
        check_10min_measurements_per_hour(
            df,
            expected_per_hour=expected_per_hour,
            raise_error=True,
        )

    numeric_df = df.select_dtypes(include=[np.number])
    hourly = numeric_df.resample(rule).mean()
    hourly.index.name = "datetime"

    return hourly


def find_missing_hours(df_hourly: pd.DataFrame) -> pd.DatetimeIndex:
    """
    Identifie les heures absentes dans une série horaire.

    Returns
    -------
    pd.DatetimeIndex
        Index des heures manquantes entre le début et la fin de la série.
    """
    ensure_datetime_index(df_hourly)

    expected_index = pd.date_range(
        start=df_hourly.index.min(),
        end=df_hourly.index.max(),
        freq="1h",
    )
    return expected_index.difference(df_hourly.index)


def handle_missing_values(
    df: pd.DataFrame,
    *,
    interpolation_limit: int = 3,
    ffill_limit: int = 3,
    drop_remaining: bool = True,
) -> pd.DataFrame:
    """
    Gère prudemment les valeurs manquantes d'une série temporelle.

    Stratégie :
    1. interpolation temporelle limitée pour petits trous ;
    2. forward fill limité ;
    3. suppression optionnelle des lignes restantes.

    Le backfill global n'est pas utilisé par défaut afin d'éviter d'utiliser
    une information future pour reconstruire le passé.

    Parameters
    ----------
    df:
        Dataset horaire indexé par datetime.
    interpolation_limit:
        Nombre maximal de périodes consécutives interpolées.
    ffill_limit:
        Nombre maximal de périodes propagées vers l'avant.
    drop_remaining:
        Si True, supprime les lignes contenant encore des NaN.

    Returns
    -------
    pd.DataFrame
        Dataset nettoyé.
    """
    ensure_datetime_index(df)

    clean = df.copy()
    clean = clean.interpolate(
        method="time",
        limit=interpolation_limit,
        limit_direction="forward",
    )
    clean = clean.ffill(limit=ffill_limit)

    if drop_remaining:
        clean = clean.dropna()

    return clean


def check_physical_ranges(df: pd.DataFrame) -> pd.Series:
    """
    Contrôle les valeurs physiquement incohérentes.

    Returns
    -------
    pd.Series
        Nombre de valeurs incohérentes par règle de contrôle.
    """
    checks = {}

    for col in ["zone1_power", "zone2_power", "zone3_power", "target", "total_load"]:
        if col in df.columns:
            checks[f"negative_{col}"] = int((df[col] < 0).sum())

    if "humidity" in df.columns:
        checks["humidity_out_of_range"] = int((~df["humidity"].between(0, 100)).sum())

    if "temperature" in df.columns:
        checks["temperature_out_of_range"] = int(
            (~df["temperature"].between(-10, 55)).sum()
        )

    if "wind_speed" in df.columns:
        checks["negative_wind_speed"] = int((df["wind_speed"] < 0).sum())

    return pd.Series(checks, name="count").astype(int)


def detect_rolling_outliers(
    series: pd.Series,
    *,
    window: int = 24,
    threshold: float = 3.5,
    min_periods: Optional[int] = None,
    use_past_only: bool = True,
) -> tuple[pd.Series, pd.Series]:
    """
    Détecte les anomalies avec un Z-score glissant.

    Par défaut, la fenêtre utilise uniquement le passé grâce à `shift(1)`.
    Cela évite d'utiliser la valeur courante ou des valeurs futures pour
    calculer le contexte de comparaison.

    Parameters
    ----------
    series:
        Série temporelle.
    window:
        Taille de la fenêtre glissante.
    threshold:
        Seuil absolu de Z-score.
    min_periods:
        Nombre minimal d'observations dans la fenêtre.
    use_past_only:
        Si True, la fenêtre est calculée sur `series.shift(1)`.

    Returns
    -------
    tuple[pd.Series, pd.Series]
        Masque booléen des outliers et série des Z-scores absolus.
    """
    if min_periods is None:
        min_periods = max(3, window // 2)

    reference = series.shift(1) if use_past_only else series

    rolling_mean = reference.rolling(window=window, min_periods=min_periods).mean()
    rolling_std = reference.rolling(window=window, min_periods=min_periods).std()
    rolling_std = rolling_std.replace(0, np.nan)

    zscore = ((series - rolling_mean) / rolling_std).abs()
    outlier_mask = (zscore > threshold).fillna(False)

    return outlier_mask.astype(bool), zscore


def summarize_outliers(
    df: pd.DataFrame,
    *,
    columns: Optional[Iterable[str]] = None,
    window: int = 24,
    threshold: float = 3.5,
) -> pd.DataFrame:
    """
    Résume le nombre d'anomalies détectées par variable.

    Returns
    -------
    pd.DataFrame
        Tableau trié par nombre d'anomalies décroissant.
    """
    if columns is None:
        columns = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    summary = {}
    for col in columns:
        mask, _ = detect_rolling_outliers(
            df[col],
            window=window,
            threshold=threshold,
            use_past_only=True,
        )
        summary[col] = int(mask.sum())

    return (
        pd.Series(summary, name="outlier_count")
        .sort_values(ascending=False)
        .to_frame()
    )


def annotate_load_outliers(
    df: pd.DataFrame,
    *,
    target_col: str = "target",
    total_load_col: str = "total_load",
    window: int = 24,
    threshold: float = 3.5,
    fill_initial_zscore: float = 0.0,
) -> pd.DataFrame:
    """
    Ajoute des colonnes d'annotation des pics/anomalies de charge.

    Les pics ne sont pas supprimés : ils sont conservés comme information métier.
    Les colonnes créées ne doivent pas être utilisées directement comme features
    prédictives si elles ne sont pas disponibles au moment de la prédiction.

    Returns
    -------
    pd.DataFrame
        Dataset avec colonnes z-score et indicateurs d'outliers.
    """
    clean = df.copy()

    target_mask, target_zscore = detect_rolling_outliers(
        clean[target_col],
        window=window,
        threshold=threshold,
        use_past_only=True,
    )

    total_mask, total_zscore = detect_rolling_outliers(
        clean[total_load_col],
        window=window,
        threshold=threshold,
        use_past_only=True,
    )

    clean["target_rolling_zscore"] = target_zscore.fillna(fill_initial_zscore)
    clean["total_load_rolling_zscore"] = total_zscore.fillna(fill_initial_zscore)

    clean["is_target_outlier"] = target_mask.astype(int)
    clean["is_total_load_outlier"] = total_mask.astype(int)
    clean["is_load_outlier"] = (
        (clean["is_target_outlier"] == 1)
        | (clean["is_total_load_outlier"] == 1)
    ).astype(int)

    return clean


def validate_clean_hourly_dataset(
    df: pd.DataFrame,
    *,
    require_no_missing: bool = True,
    require_no_duplicates: bool = True,
    require_hourly_frequency: bool = True,
) -> dict:
    """
    Valide strictement le dataset horaire avant sauvegarde.

    Raises
    ------
    ValueError
        Si une condition stricte n'est pas respectée.

    Returns
    -------
    dict
        Résumé de validation.
    """
    ensure_datetime_index(df)

    missing_total = int(df.isna().sum().sum())
    duplicated_total = int(df.index.duplicated().sum())
    inferred_frequency = pd.infer_freq(df.index)

    if require_no_missing and missing_total > 0:
        raise ValueError(f"Dataset non propre : {missing_total} valeurs manquantes.")

    if require_no_duplicates and duplicated_total > 0:
        raise ValueError(f"Dataset non propre : {duplicated_total} doublons temporels.")

    if require_hourly_frequency and not is_hourly_frequency(inferred_frequency):
        raise ValueError(f"Fréquence horaire invalide : {inferred_frequency}")

    return {
        "missing_total": missing_total,
        "duplicated_total": duplicated_total,
        "inferred_frequency": str(inferred_frequency),
        "n_rows": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "start_date": str(df.index.min()),
        "end_date": str(df.index.max()),
    }


def temporal_train_val_test_split(
    df: pd.DataFrame,
    *,
    train_size: float = 0.70,
    val_size: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Découpe un dataset temporel en train, validation et test sans shuffle.

    Parameters
    ----------
    df:
        Dataset temporel trié.
    train_size:
        Proportion du train.
    val_size:
        Proportion de validation.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Train, validation et test.
    """
    ensure_datetime_index(df)

    if train_size <= 0 or val_size <= 0 or train_size + val_size >= 1:
        raise ValueError("Les proportions train/validation/test sont invalides.")

    n = len(df)
    train_end = int(n * train_size)
    val_end = int(n * (train_size + val_size))

    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()

    return train_df, val_df, test_df


def get_base_feature_columns(
    df: pd.DataFrame,
    *,
    allowed_features: Optional[Iterable[str]] = None,
    forbidden_features: Optional[Iterable[str]] = None,
) -> list[str]:
    """
    Retourne les variables météo autorisées pour le scaling de base.

    Les colonnes de consommation instantanée sont volontairement exclues pour
    éviter la fuite de données. Elles seront utilisées plus tard uniquement
    sous forme de lags ou de rolling features basées sur le passé.
    """
    if allowed_features is None:
        allowed_features = BASE_WEATHER_FEATURES

    if forbidden_features is None:
        forbidden_features = FORBIDDEN_DIRECT_FEATURES

    missing = sorted(set(allowed_features) - set(df.columns))
    if missing:
        raise ValueError(f"Features attendues absentes : {missing}")

    feature_cols = list(allowed_features)
    leakage_cols = sorted(set(feature_cols).intersection(forbidden_features))
    if leakage_cols:
        raise ValueError(f"Data leakage détecté dans les features : {leakage_cols}")

    return feature_cols


def scale_train_val_test(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    *,
    feature_cols: Iterable[str],
    target_col: str = "target",
    scaler_type: Literal["standard", "minmax"] = "standard",
) -> dict:
    """
    Normalise les features et la cible sans fuite de données.

    Règle :
    - fit uniquement sur train ;
    - transform sur validation et test.

    Returns
    -------
    dict
        DataFrames normalisés et scalers ajustés.
    """
    feature_cols = list(feature_cols)

    if scaler_type == "standard":
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
    elif scaler_type == "minmax":
        scaler_X = MinMaxScaler()
        scaler_y = MinMaxScaler()
    else:
        raise ValueError("scaler_type doit être 'standard' ou 'minmax'.")

    X_train = pd.DataFrame(
        scaler_X.fit_transform(train_df[feature_cols]),
        index=train_df.index,
        columns=feature_cols,
    )
    X_val = pd.DataFrame(
        scaler_X.transform(val_df[feature_cols]),
        index=val_df.index,
        columns=feature_cols,
    )
    X_test = pd.DataFrame(
        scaler_X.transform(test_df[feature_cols]),
        index=test_df.index,
        columns=feature_cols,
    )

    y_train = pd.DataFrame(
        scaler_y.fit_transform(train_df[[target_col]]),
        index=train_df.index,
        columns=[target_col],
    )
    y_val = pd.DataFrame(
        scaler_y.transform(val_df[[target_col]]),
        index=val_df.index,
        columns=[target_col],
    )
    y_test = pd.DataFrame(
        scaler_y.transform(test_df[[target_col]]),
        index=test_df.index,
        columns=[target_col],
    )

    return {
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
        "scaler_X": scaler_X,
        "scaler_y": scaler_y,
        "feature_cols": feature_cols,
        "target_col": target_col,
    }


def save_preprocessing_outputs(
    *,
    output_dir: str | Path,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    scaled_outputs: Optional[dict] = None,
) -> dict:
    """
    Sauvegarde les datasets propres et, optionnellement, les fichiers normalisés.

    Returns
    -------
    dict
        Chemins des fichiers sauvegardés.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "clean_full": output_dir / "tetouan_hourly_clean.csv",
        "train_clean": output_dir / "train_clean.csv",
        "val_clean": output_dir / "val_clean.csv",
        "test_clean": output_dir / "test_clean.csv",
    }

    clean_df.to_csv(paths["clean_full"], index=True)
    train_df.to_csv(paths["train_clean"], index=True)
    val_df.to_csv(paths["val_clean"], index=True)
    test_df.to_csv(paths["test_clean"], index=True)

    if scaled_outputs is not None:
        for key in ["X_train", "X_val", "X_test", "y_train", "y_val", "y_test"]:
            if key in scaled_outputs:
                path = output_dir / f"{key}_scaled_base.csv"
                scaled_outputs[key].to_csv(path, index=True)
                paths[key] = path

    return {key: str(value) for key, value in paths.items()}


def save_scalers(
    *,
    scaler_X,
    scaler_y,
    models_dir: str | Path,
    prefix: str = "base",
) -> dict:
    """
    Sauvegarde les scalers ajustés uniquement sur le train.
    """
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    scaler_X_path = models_dir / f"scaler_X_{prefix}.pkl"
    scaler_y_path = models_dir / f"scaler_y_{prefix}.pkl"

    joblib.dump(scaler_X, scaler_X_path)
    joblib.dump(scaler_y, scaler_y_path)

    return {
        "scaler_X": str(scaler_X_path),
        "scaler_y": str(scaler_y_path),
    }


def preprocessing_pipeline(
    df_10min: pd.DataFrame,
    *,
    train_size: float = 0.70,
    val_size: float = 0.15,
    target_col: str = "target",
    outlier_window: int = 24,
    outlier_threshold: float = 3.5,
) -> dict:
    """
    Pipeline complet de prétraitement, sans écriture disque.

    Parameters
    ----------
    df_10min:
        Dataset chargé avec `load_tetouan_data`, indexé à 10 minutes.
    train_size:
        Proportion du train.
    val_size:
        Proportion de validation.
    target_col:
        Colonne cible.
    outlier_window:
        Fenêtre du Z-score glissant.
    outlier_threshold:
        Seuil d'anomalie.

    Returns
    -------
    dict
        Objets principaux du preprocessing : datasets, splits, scalers et rapport.
    """
    hourly_counts = check_10min_measurements_per_hour(df_10min)
    df_hourly = resample_hourly(df_10min, check_counts=False)

    missing_hours = find_missing_hours(df_hourly)
    df_clean = handle_missing_values(df_hourly)
    df_clean = annotate_load_outliers(
        df_clean,
        target_col=target_col,
        total_load_col="total_load",
        window=outlier_window,
        threshold=outlier_threshold,
    )

    validation_report = validate_clean_hourly_dataset(df_clean)
    physical_checks = check_physical_ranges(df_clean)
    outlier_summary = summarize_outliers(df_clean)

    train_df, val_df, test_df = temporal_train_val_test_split(
        df_clean,
        train_size=train_size,
        val_size=val_size,
    )

    feature_cols = get_base_feature_columns(df_clean)
    scaled_outputs = scale_train_val_test(
        train_df,
        val_df,
        test_df,
        feature_cols=feature_cols,
        target_col=target_col,
    )

    report = {
        "hourly_counts_distribution": {
            str(k): int(v) for k, v in hourly_counts.value_counts().sort_index().items()
        },
        "missing_hours": int(len(missing_hours)),
        "validation_report": validation_report,
        "physical_checks": {str(k): int(v) for k, v in physical_checks.items()},
        "outlier_summary": {
            str(k): int(v) for k, v in outlier_summary["outlier_count"].items()
        },
        "train_shape": list(train_df.shape),
        "val_shape": list(val_df.shape),
        "test_shape": list(test_df.shape),
        "feature_cols_base": feature_cols,
        "forbidden_direct_features": FORBIDDEN_DIRECT_FEATURES,
    }

    return {
        "df_hourly": df_hourly,
        "df_clean": df_clean,
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,
        "scaled_outputs": scaled_outputs,
        "report": report,
    }
