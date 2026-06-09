"""
src/data_loader.py

Fonctions de chargement, validation et audit du dataset
Power Consumption of Tetouan City.

Ce module correspond à la partie "dataset / audit qualité" du projet.
Les notebooks peuvent l'utiliser au lieu de dupliquer le code de chargement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd


COLUMN_MAPPING: Dict[str, str] = {
    "DateTime": "datetime",
    "Temperature": "temperature",
    "Humidity": "humidity",
    "Wind Speed": "wind_speed",
    "general diffuse flows": "general_diffuse_flows",
    "diffuse flows": "diffuse_flows",
    "Zone 1 Power Consumption": "zone1_power",
    "Zone 2 Power Consumption": "zone2_power",
    "Zone 3 Power Consumption": "zone3_power",
}

NUMERIC_COLUMNS = [
    "temperature",
    "humidity",
    "wind_speed",
    "general_diffuse_flows",
    "diffuse_flows",
    "zone1_power",
    "zone2_power",
    "zone3_power",
]

EXPECTED_COLUMNS = ["datetime"] + NUMERIC_COLUMNS


def normalize_raw_column_names(columns: Iterable[str]) -> list[str]:
    """
    Standardise les noms de colonnes bruts avant le renommage.

    Le fichier Tetouan peut contenir des espaces multiples dans les colonnes
    Zone 2 et Zone 3. Cette fonction supprime les espaces au début/à la fin
    et remplace les séquences d'espaces par un seul espace.

    Parameters
    ----------
    columns:
        Noms de colonnes du fichier CSV.

    Returns
    -------
    list[str]
        Noms de colonnes normalisés.
    """
    return (
        pd.Index(columns)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .tolist()
    )


def check_required_columns(columns: Iterable[str]) -> None:
    """
    Vérifie que toutes les colonnes nécessaires sont présentes après nettoyage.

    Parameters
    ----------
    columns:
        Noms de colonnes du DataFrame brut après normalisation des espaces.

    Raises
    ------
    ValueError
        Si au moins une colonne obligatoire manque.
    """
    columns_set = set(columns)
    missing = [col for col in COLUMN_MAPPING if col not in columns_set]
    if missing:
        raise ValueError(
            "Colonnes manquantes dans le fichier Tetouan : "
            + ", ".join(missing)
        )


def load_tetouan_data(
    path: str | Path,
    *,
    set_datetime_index: bool = True,
    strict_frequency: bool = False,
    datetime_format: Optional[str] = "%m/%d/%Y %H:%M",
    create_target: bool = True,
    drop_duplicate_datetimes: bool = True,
) -> pd.DataFrame:
    """
    Charge et prépare le dataset Power Consumption of Tetouan City.

    Étapes réalisées :
    1. lecture du CSV ;
    2. nettoyage des noms de colonnes ;
    3. vérification des colonnes attendues ;
    4. renommage technique ;
    5. conversion de la date ;
    6. conversion numérique ;
    7. tri chronologique ;
    8. suppression éventuelle des doublons temporels ;
    9. création de `target` et `total_load` ;
    10. indexation temporelle optionnelle.

    Parameters
    ----------
    path:
        Chemin du fichier CSV brut.
    set_datetime_index:
        Si True, `datetime` devient l'index temporel.
    strict_frequency:
        Si True, lève une erreur si la fréquence inférée n'est pas 10 minutes.
    datetime_format:
        Format attendu pour la colonne DateTime. Mettre None pour laisser
        pandas inférer automatiquement.
    create_target:
        Si True, crée `target = zone1_power` et `total_load`.
    drop_duplicate_datetimes:
        Si True, supprime les doublons temporels en conservant la première
        occurrence.

    Returns
    -------
    pd.DataFrame
        Dataset propre, trié et prêt pour l'audit, l'EDA ou le preprocessing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    df = pd.read_csv(path)
    df.columns = normalize_raw_column_names(df.columns)

    check_required_columns(df.columns)

    df = df.rename(columns=COLUMN_MAPPING)

    if datetime_format is None:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    else:
        df["datetime"] = pd.to_datetime(
            df["datetime"],
            format=datetime_format,
            errors="coerce",
        )

    invalid_dates = int(df["datetime"].isna().sum())
    if invalid_dates > 0:
        raise ValueError(f"{invalid_dates} dates non convertibles détectées.")

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    numeric_missing = int(df[NUMERIC_COLUMNS].isna().sum().sum())
    if numeric_missing > 0:
        raise ValueError(
            f"{numeric_missing} valeurs numériques non convertibles détectées."
        )

    df = df.sort_values("datetime").reset_index(drop=True)

    duplicated_count = int(df["datetime"].duplicated().sum())
    if duplicated_count > 0 and drop_duplicate_datetimes:
        df = df.drop_duplicates(subset="datetime", keep="first").reset_index(drop=True)

    if create_target:
        df["target"] = df["zone1_power"]
        df["total_load"] = (
            df["zone1_power"] + df["zone2_power"] + df["zone3_power"]
        )

    inferred_frequency = pd.infer_freq(df["datetime"])
    df.attrs["duplicated_datetime_count"] = duplicated_count
    df.attrs["inferred_frequency"] = inferred_frequency
    df.attrs["invalid_dates"] = invalid_dates

    if strict_frequency and inferred_frequency not in {"10min", "10T"}:
        raise ValueError(
            "Fréquence attendue : 10 minutes ; "
            f"fréquence inférée : {inferred_frequency}"
        )

    if set_datetime_index:
        df = df.set_index("datetime")
        df.index.name = "datetime"

    return df


def audit_tetouan_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produit un tableau d'audit qualité par colonne.

    Parameters
    ----------
    df:
        Dataset Tetouan chargé avec `load_tetouan_data`.

    Returns
    -------
    pd.DataFrame
        Tableau avec type, valeurs manquantes, taux de manquants
        et statistiques descriptives lorsque disponibles.
    """
    audit = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "missing_count": df.isna().sum(),
            "missing_rate_pct": (df.isna().mean() * 100).round(4),
        }
    )

    numeric_summary = df.describe().T
    useful_stats = [
        col for col in ["min", "mean", "50%", "max", "std"] if col in numeric_summary
    ]
    audit = audit.join(numeric_summary[useful_stats], how="left")

    return audit


def dataset_quality_summary(df: pd.DataFrame) -> dict:
    """
    Retourne un résumé global de qualité du dataset.

    Parameters
    ----------
    df:
        Dataset indexé par datetime ou contenant une colonne `datetime`.

    Returns
    -------
    dict
        Indicateurs principaux : dimensions, période, fréquence,
        valeurs manquantes et doublons temporels.
    """
    if isinstance(df.index, pd.DatetimeIndex):
        datetime_values = df.index
        duplicated_datetime = int(df.index.duplicated().sum())
    elif "datetime" in df.columns:
        datetime_values = pd.to_datetime(df["datetime"], errors="coerce")
        duplicated_datetime = int(datetime_values.duplicated().sum())
    else:
        raise ValueError("Le DataFrame doit avoir un DatetimeIndex ou une colonne datetime.")

    return {
        "n_rows": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "start_date": str(datetime_values.min()),
        "end_date": str(datetime_values.max()),
        "inferred_frequency": str(pd.infer_freq(datetime_values)),
        "missing_total": int(df.isna().sum().sum()),
        "duplicated_datetime": duplicated_datetime,
    }


if __name__ == "__main__":
    data_path = Path("data/raw/Tetuan City power consumption.csv")
    data = load_tetouan_data(data_path, strict_frequency=True)
    print(dataset_quality_summary(data))
    print(audit_tetouan_data(data))
