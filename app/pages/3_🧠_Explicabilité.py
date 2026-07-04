import streamlit as st
import pandas as pd
import shap
import matplotlib.pyplot as plt
from utils import load_css, load_features_dataset, load_xgb_model, load_predictions

st.set_page_config(page_title="Explicabilité", page_icon="🧠", layout="wide")
load_css()

st.markdown("<h1>🧠 Explicabilité du Modèle (XAI)</h1>", unsafe_allow_html=True)
st.markdown("Plongez dans le cerveau de l'Intelligence Artificielle. Comprenez pourquoi XGBoost a pris cette décision à l'aide des valeurs SHAP.")

# Chargement
df_features = load_features_dataset()
xgb_model, feature_names = load_xgb_model()
preds = load_predictions()

test_start = preds.index.min()
df_test = df_features.loc[test_start:]

st.sidebar.header("Analyse Locale (SHAP)")
available_dates = df_test.index.date
selected_date = st.sidebar.selectbox("Date", list(dict.fromkeys(available_dates)))

hours_for_date = df_test[df_test.index.date == selected_date].index.hour
selected_hour = st.sidebar.selectbox("Heure", hours_for_date)

selected_datetime = pd.to_datetime(f"{selected_date} {selected_hour:02d}:00:00")

if selected_datetime in df_test.index:
    row = df_test.loc[[selected_datetime], feature_names]
    pred_value = xgb_model.predict(row)[0]
    
    st.markdown(f"### Analyse de la prédiction pour le {selected_datetime.strftime('%d/%m/%Y à %H:%M')}")
    st.metric("Charge Prédite", f"{pred_value:.0f} kW")
    
    st.markdown("Ce graphique (Waterfall) détaille comment chaque variable a contribué à pousser la prédiction depuis la moyenne globale jusqu'à la valeur finale de ce moment précis.")
    
    with st.spinner("Calcul des valeurs SHAP locales..."):
        explainer = shap.TreeExplainer(xgb_model)
        shap_values = explainer(row)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Style sombre pour matplotlib
        plt.style.use('dark_background')
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        shap.plots.waterfall(shap_values[0], show=False)
        st.pyplot(fig)
        plt.clf()
else:
    st.error("Cette heure n'existe pas dans le jeu de test.")

st.markdown("---")
st.markdown("### Importance Globale des Variables")
st.markdown("Ce graphique interactif montre l'importance moyenne (impact absolu) de chaque variable sur l'ensemble du dataset.")
# Image statique précalculée (c'est plus performant pour l'importance globale qui ne change pas)
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
global_shap_path = PROJECT_ROOT / "results" / "figures" / "14_shap_global_importance.png"
if global_shap_path.exists():
    st.image(str(global_shap_path), use_column_width=True)
else:
    st.info("L'image de l'importance globale SHAP n'est pas disponible.")
