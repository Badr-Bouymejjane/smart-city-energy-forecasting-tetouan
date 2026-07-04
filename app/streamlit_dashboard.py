from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.data_loader import load_tetouan_data
from src.preprocessing import resample_hourly
from src.features import create_features

st.set_page_config(
    page_title="Tetouan Smart City Energy Forecasting",
    layout="wide",
)

st.title("Smart City — Prévision de la charge énergétique à Tétouan")

st.markdown(
    """
    Ce dashboard est un prototype pédagogique. Il permet de charger le CSV Tetouan,
    visualiser les consommations des trois zones, afficher quelques indicateurs
    de risque et préparer les données pour la modélisation.
    """
)

uploaded_file = st.file_uploader(
    "Uploader le fichier Tetuan City power consumption.csv",
    type=["csv"],
)

if uploaded_file is not None:
    raw_path = PROJECT_ROOT / "data" / "raw" / "uploaded_tetouan.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(uploaded_file.getvalue())

    df = load_tetouan_data(raw_path)
    hourly = resample_hourly(df)
    featured = create_features(hourly, target_col="target", drop_na=True)

    st.subheader("Aperçu des données")
    st.dataframe(df.head())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Observations brutes", f"{len(df):,}")
    col2.metric("Observations horaires", f"{len(hourly):,}")
    col3.metric("Début", str(df.index.min()))
    col4.metric("Fin", str(df.index.max()))

    st.subheader("Consommation par zone")
    st.line_chart(hourly[["zone1_power", "zone2_power", "zone3_power"]])

    st.subheader("Variables météo")
    st.line_chart(hourly[["temperature", "humidity", "wind_speed"]])

    st.subheader("Analyse simple du risque de pic")
    threshold = hourly["target"].quantile(0.95)
    latest_value = hourly["target"].iloc[-1]

    if latest_value >= threshold:
        st.error("Alerte : consommation récente dans la zone de pic historique.")
        st.write(
            "Recommandation : surveiller la charge, éviter les usages non critiques "
            "et préparer une action de réduction préventive."
        )
    else:
        st.success("Charge récente sous le seuil de pic historique.")
        st.write("Recommandation : poursuivre la surveillance normale.")

    st.subheader("Dataset enrichi pour modélisation")
    st.dataframe(featured.tail())

else:
    st.info("Veuillez uploader le fichier CSV Tetouan pour démarrer.")
