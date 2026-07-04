import streamlit as st
import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path

# Chemins
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"

@st.cache_data
def load_css():
    css_file = PROJECT_ROOT / "app" / "assets" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache_data
def load_dataset():
    """Charge le dataset nettoyé horaire et crée la cible si nécessaire"""
    df_path = PROCESSED_DIR / "tetouan_hourly_clean.csv"
    if not df_path.exists():
        df_path = PROCESSED_DIR / "tetouan_hourly.csv"
        
    df = pd.read_csv(df_path)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime")
    else:
        # Fallback si l'index n'est pas nommé datetime
        first_col = df.columns[0]
        df[first_col] = pd.to_datetime(df[first_col])
        df = df.set_index(first_col)
        df.index.name = "datetime"
        
    df = df.sort_index()
    
    if "target" not in df.columns and "zone1_power" in df.columns:
        df["target"] = df["zone1_power"]
        
    return df

@st.cache_data
def load_features_dataset():
    """Charge le dataset complet avec toutes les features"""
    df_path = PROCESSED_DIR / "tetouan_features.csv"
    df = pd.read_csv(df_path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    return df

@st.cache_resource
def load_xgb_model():
    """Charge le modèle XGBoost et la liste de ses features"""
    model_path = MODELS_DIR / "xgboost_model.pkl"
    features_path = MODELS_DIR / "ml_feature_names.json"
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        
    with open(features_path, "r") as f:
        feature_names = json.load(f)["feature_names"]
        
    return model, feature_names

@st.cache_data
def load_predictions():
    """Charge les prédictions finales du test set"""
    pred_path = RESULTS_DIR / "predictions" / "xgboost_predictions.csv"
    preds = pd.read_csv(pred_path)
    preds["datetime"] = pd.to_datetime(preds["datetime"])
    preds = preds.set_index("datetime")
    return preds

@st.cache_data
def get_p95_threshold():
    """Calcule le seuil du 95e percentile de la charge"""
    df = load_dataset()
    return df["target"].quantile(0.95)
