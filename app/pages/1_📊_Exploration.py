import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_css, load_dataset

st.set_page_config(page_title="Exploration", page_icon="📊", layout="wide")
load_css()

st.markdown("<h1>📊 Exploration des Données (EDA)</h1>", unsafe_allow_html=True)
st.markdown("Analysez les tendances historiques de la consommation énergétique.")

df = load_dataset()

# Filtre temporel dynamique dans la sidebar
st.sidebar.header("Filtres")
min_date = df.index.min().date()
max_date = df.index.min().date() + pd.Timedelta(days=30) # Par défaut, le premier mois

date_range = st.sidebar.date_input(
    "Période",
    value=(min_date, max_date),
    min_value=df.index.min().date(),
    max_value=df.index.max().date()
)

if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df.index.date >= start_date) & (df.index.date <= end_date)
    df_filtered = df.loc[mask].copy()
    
    st.subheader(f"Série temporelle ({start_date} au {end_date})")
    
    # Graphique interactif Plotly
    fig = px.line(df_filtered, y="target", labels={"target": "Consommation (kW)", "datetime": "Date"},
                  title="Évolution de la consommation électrique (Zone 1)")
    fig.update_traces(line_color="#00d2ff")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Consommation Moyenne par Heure")
        df_filtered["hour"] = df_filtered.index.hour
        hourly_mean = df_filtered.groupby("hour")["target"].mean().reset_index()
        fig_hour = px.bar(hourly_mean, x="hour", y="target", 
                          color="target", color_continuous_scale="Blues",
                          labels={"target": "kW moyen", "hour": "Heure"})
        fig_hour.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_hour, use_container_width=True)
        
    with col2:
        st.subheader("Température vs Consommation")
        fig_scatter = px.scatter(df_filtered, x="temperature", y="target", 
                                 opacity=0.6, color="temperature", color_continuous_scale="Turbo")
        fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("Veuillez sélectionner une date de début et de fin.")
