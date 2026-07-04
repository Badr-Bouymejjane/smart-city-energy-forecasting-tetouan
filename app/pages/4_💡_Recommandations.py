import streamlit as st
from utils import load_css

st.set_page_config(page_title="Recommandations", page_icon="💡", layout="wide")
load_css()

st.markdown("<h1>💡 Recommandations Métier & Smart Grid</h1>", unsafe_allow_html=True)
st.markdown("L'objectif final de l'intelligence artificielle est d'automatiser et de sécuriser la prise de décision.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔌 1. Load Shedding (Délestage Préventif)")
    st.markdown("""
    En cas d'alerte rouge générée par le simulateur (Page 2), le gestionnaire de réseau doit :
    * Réduire l'éclairage public dans les parcs et zones non critiques de 20%.
    * Décaler le démarrage des pompes de traitement des eaux municipales.
    * Réduire la climatisation des bâtiments publics de 1 à 2°C de manière invisible.
    """)
    
    st.markdown("### 📣 2. Sensibilisation Citoyenne")
    st.markdown("""
    La Smart City implique ses habitants :
    * Envoi de notifications Push ("Pic de chaleur attendu à 14h, décalez vos machines").
    * Offres tarifaires dynamiques (Heures creuses variables selon la météo).
    """)

with col2:
    st.markdown("### 🏗️ 3. Planification Énergétique")
    st.markdown("""
    Grâce à l'historique et aux prévisions à 24h, la ville peut :
    * Acheter l'énergie sur le marché de gros au moment où elle est la moins chère.
    * Charger les batteries géantes (si la ville en dispose) pendant la nuit (00h-05h).
    * Dimensionner avec précision la part des énergies renouvelables (solaire) pour le lendemain.
    """)
    
    st.markdown("### 🛠️ 4. Maintenance Ciblée")
    st.markdown("""
    L'analyse des heures de pointe (Pointe du soir : 18h-21h) dicte le calendrier :
    * Aucune opération de maintenance risquée ne doit être planifiée entre 18h et 21h.
    * Les plages de maintenance idéales sont de nuit (00h à 05h) où la charge est au plus bas.
    """)

st.markdown("---")
st.info("Ces recommandations clôturent le workflow KDD (Knowledge Discovery in Databases) en transformant une donnée mathématique brute (prédiction en kW) en une action humaine concrète et utile à la communauté.")
