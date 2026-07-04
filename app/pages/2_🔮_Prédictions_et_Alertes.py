import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import load_css, load_features_dataset, load_xgb_model, load_predictions, get_p95_threshold

st.set_page_config(page_title="Prédictions", page_icon="🔮", layout="wide")
load_css()

st.markdown("<h1>🔮 Simulateur de Prédictions & Alertes</h1>", unsafe_allow_html=True)
st.markdown("Simulez la prédiction du modèle XGBoost en temps réel et surveillez le seuil d'alerte du Smart Grid.")

# Chargement
df_features = load_features_dataset()
xgb_model, feature_names = load_xgb_model()
preds = load_predictions()
p95_threshold = get_p95_threshold()

# Isoler le set de test
test_start = preds.index.min()
df_test = df_features.loc[test_start:]

st.sidebar.header("Simulateur Temps Réel")
st.sidebar.markdown("Choisissez un moment dans le Test Set :")

# Sélection d'une date (on simule une heure précise)
available_dates = df_test.index.date
selected_date = st.sidebar.selectbox("Date", list(dict.fromkeys(available_dates)))

# Filtrer les heures disponibles pour cette date
hours_for_date = df_test[df_test.index.date == selected_date].index.hour
selected_hour = st.sidebar.selectbox("Heure", hours_for_date)

# Sélection de la ligne exacte
selected_datetime = pd.to_datetime(f"{selected_date} {selected_hour:02d}:00:00")

if selected_datetime in df_test.index:
    row = df_test.loc[[selected_datetime]]
    
    # Simulateur de température dynamique
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Simulation d'incident Météo :**")
    temp_offset = st.sidebar.slider("Ajustement Température (°C)", min_value=-10.0, max_value=15.0, value=0.0, step=0.5)
    
    # Création de la donnée modifiée
    row_simulated = row.copy()
    if temp_offset != 0:
        row_simulated["temperature"] += temp_offset
        # Recalcul simpliste de HDD/CDD si possible
        temp_base = 18.0
        row_simulated["HDD"] = max(temp_base - row_simulated["temperature"].iloc[0], 0)
        row_simulated["CDD"] = max(row_simulated["temperature"].iloc[0] - temp_base, 0)
    
    # Prédiction avec le modèle (il attend les colonnes de feature_names)
    X_input = row_simulated[feature_names]
    pred_value = xgb_model.predict(X_input)[0]
    actual_value = row["target"].iloc[0]
    
    # Affichage du résultat dynamique
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Consommation Réelle", f"{actual_value:.0f} kW")
    with col2:
        delta = pred_value - actual_value
        st.metric("Prédiction XGBoost", f"{pred_value:.0f} kW", delta=f"{delta:+.0f} kW (Erreur)", delta_color="inverse")
    with col3:
        current_temp = row_simulated["temperature"].iloc[0]
        st.metric("Température Simulée", f"{current_temp:.1f} °C", delta=f"{temp_offset:+.1f} °C")

    # Système d'Alerte Dynamique
    st.markdown("### 🚨 Statut du Réseau")
    if pred_value > p95_threshold:
        st.markdown(f"<div class='alert-box'>ALERTE CRITIQUE : Dépassement du seuil de charge (Prévision > {p95_threshold:.0f} kW). Délestage recommandé !</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='normal-box'>RESEAU STABLE : Charge nominale attendue (Seuil d'alerte : {p95_threshold:.0f} kW).</div>", unsafe_allow_html=True)

    # Affichage d'une fenêtre temporelle autour de la sélection (± 12h)
    st.markdown("### Contexte Temporel (± 12 heures)")
    context_start = selected_datetime - pd.Timedelta(hours=12)
    context_end = selected_datetime + pd.Timedelta(hours=12)
    
    context_actual = df_test.loc[context_start:context_end, "target"]
    context_preds = preds.loc[context_start:context_end, "prediction"]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=context_actual.index, y=context_actual, mode='lines', name='Réel (Historique)', line=dict(color='gray', dash='dash')))
    fig.add_trace(go.Scatter(x=context_preds.index, y=context_preds, mode='lines', name='Prédiction Normale', line=dict(color='#00d2ff')))
    
    # Point simulé
    fig.add_trace(go.Scatter(x=[selected_datetime], y=[pred_value], mode='markers', name='Prédiction Simulée', 
                             marker=dict(color='red', size=15, symbol='star')))
    
    # Ligne de seuil
    fig.add_hline(y=p95_threshold, line_dash="dot", line_color="red", annotation_text="Seuil d'Alerte (P95)")
    
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Cette heure n'existe pas dans le jeu de test.")
