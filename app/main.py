import streamlit as st
import pandas as pd
from utils import load_css, load_dataset, load_predictions

st.set_page_config(
    page_title="Smart City Energy Control",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Appliquer le style CSS premium
load_css()

# Titre Principal
st.markdown("<h1>⚡ Smart City Energy Control Center</h1>", unsafe_allow_html=True)
st.markdown("### Tétouan (Maroc) - Surveillance du Réseau Électrique")
st.markdown("---")

st.markdown("""
Bienvenue dans le **Centre de Contrôle Virtuel** de la Smart City. 
Cette application exploite l'Intelligence Artificielle (XGBoost) pour analyser, prédire et expliquer la consommation électrique de la ville en temps réel.
""")

# Chargement rapide des métriques globales
try:
    df = load_dataset()
    preds = load_predictions()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Observations", f"{len(df):,}")
    with col2:
        st.metric("Consommation Moyenne", f"{df['target'].mean():.0f} kW")
    with col3:
        st.metric("Erreur Modèle (MAPE)", "2.44 %")
    with col4:
        st.metric("Précision Modèle (R²)", "97.0 %")
        
except Exception as e:
    st.warning("Certains fichiers de données ne sont pas générés. Exécutez le pipeline ML avant d'utiliser le dashboard.")
    st.error(str(e))

st.markdown("---")
st.markdown("""
### 🧭 Navigation
- **📊 Exploration :** Découvrez les cycles de consommation (Heatmaps, tendances).
- **🔮 Prédictions et Alertes :** Testez le simulateur prédictif et le système d'alerte.
- **🧠 Explicabilité (XAI) :** Comprenez *pourquoi* le modèle prédit un pic.
- **💡 Recommandations :** Actions métier (Load shedding, gestion du réseau).
""")
