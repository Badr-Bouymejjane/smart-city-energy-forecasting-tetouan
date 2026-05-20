# Smart City Energy Forecasting — Tetouan

## 1. Description du projet

Ce projet de Data Mining vise à prédire la consommation électrique d'une zone urbaine de Tétouan dans un contexte de Smart City.

Le projet suit le processus KDD complet :

1. Sélection des données
2. Audit qualité
3. Analyse exploratoire des données
4. Prétraitement
5. Feature Engineering
6. Modélisation
7. Évaluation
8. Explicabilité XAI
9. Recommandations Smart City

Le dataset principal utilisé est :

```text
Power Consumption of Tetouan City
```

Le fichier brut attendu est :

```text
data/raw/Tetuan City power consumption.csv
```

---

## 2. Objectif principal

Construire un pipeline complet permettant de prédire la consommation électrique de la Zone 1 de Tétouan à partir :

- de l'historique de consommation ;
- des variables météorologiques ;
- des variables temporelles ;
- des cycles d'activité humaine représentés par des proxys calendaires.

La cible principale est :

```text
Zone 1 Power Consumption
```

Elle sera renommée techniquement en :

```text
zone1_power
```

Puis copiée dans :

```text
target
```

---

## 3. Dataset

### 3.1 Colonnes originales

Le fichier contient les colonnes suivantes :

- DateTime
- Temperature
- Humidity
- Wind Speed
- general diffuse flows
- diffuse flows
- Zone 1 Power Consumption
- Zone 2 Power Consumption
- Zone 3 Power Consumption

### 3.2 Renommage technique

| Colonne originale | Nom technique |
|---|---|
| DateTime | datetime |
| Temperature | temperature |
| Humidity | humidity |
| Wind Speed | wind_speed |
| general diffuse flows | general_diffuse_flows |
| diffuse flows | diffuse_flows |
| Zone 1 Power Consumption | zone1_power |
| Zone 2 Power Consumption | zone2_power |
| Zone 3 Power Consumption | zone3_power |

### 3.3 Variables créées

```text
target = zone1_power
total_load = zone1_power + zone2_power + zone3_power
```

---

## 4. Architecture du projet

```text
smart-city-energy-forecasting-tetouan/
│
├── README.md
├── requirements.txt
├── .gitignore
├── config.yaml
│
├── data/
│   ├── raw/
│   │   └── Tetuan City power consumption.csv
│   ├── processed/
│   │   ├── tetouan_hourly.csv
│   │   └── tetouan_features.csv
│   └── external/
│       └── holidays_morocco.csv
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_preprocessing.ipynb
│   ├── 04_feature_engineering.ipynb
│   ├── 05_modeling_sarima_prophet.ipynb
│   ├── 06_modeling_ml_xgboost.ipynb
│   ├── 07_modeling_gru.ipynb
│   ├── 08_xai_shap_lime.ipynb
│   └── 09_results_and_recommendations.ipynb
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── features.py
│   ├── models_baseline.py
│   ├── models_sarima.py
│   ├── models_prophet.py
│   ├── models_ml.py
│   ├── models_gru.py
│   ├── evaluation.py
│   ├── xai.py
│   └── utils.py
│
├── models/
├── results/
├── reports/
└── app/
    └── streamlit_dashboard.py
```

---

## 5. Installation

### 5.1 Créer un environnement virtuel

```bash
python -m venv .venv
```

Activer l'environnement :

#### Linux / macOS / Git Bash

```bash
source .venv/bin/activate
```

#### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### 5.2 Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Exécution des notebooks

Lancer Jupyter :

```bash
jupyter notebook
```

Ordre recommandé :

```text
notebooks/01_data_audit.ipynb
notebooks/02_eda.ipynb
notebooks/03_preprocessing.ipynb
notebooks/04_feature_engineering.ipynb
notebooks/05_modeling_sarima_prophet.ipynb
notebooks/06_modeling_ml_xgboost.ipynb
notebooks/07_modeling_gru.ipynb
notebooks/08_xai_shap_lime.ipynb
notebooks/09_results_and_recommendations.ipynb
```

---

## 7. Modèles prévus

Le projet comparera plusieurs familles de modèles :

| Modèle | Rôle |
|---|---|
| Naive Forecast | Baseline minimale |
| SARIMA / SARIMAX | Modèle statistique temporel |
| Prophet | Modèle additif avec saisonnalités |
| Random Forest | Modèle ML robuste |
| XGBoost | Modèle ML performant |
| GRU | Modèle Deep Learning séquentiel |

---

## 8. Métriques d'évaluation

Les métriques principales sont :

- MAE
- RMSE
- MAPE
- R² optionnel

L'évaluation doit respecter l'ordre temporel des données. Aucun shuffle ne doit être utilisé.

---

## 9. Explicabilité

L'explicabilité sera réalisée avec :

- SHAP pour XGBoost ou Random Forest ;
- LIME en complément si nécessaire.

Objectif : expliquer les facteurs qui influencent une prédiction de pic de consommation.

---

## 10. Dashboard Streamlit

Le dashboard final sera placé dans :

```text
app/streamlit_dashboard.py
```

Lancement :

```bash
streamlit run app/streamlit_dashboard.py
```

---

## 11. Résultats attendus

Les résultats seront sauvegardés dans :

```text
results/figures/
results/tables/
results/metrics/
results/predictions/
```

Les modèles entraînés seront sauvegardés dans :

```text
models/
```

---

## 12. Auteurs

Projet réalisé dans le cadre du module Data Mining.

### Binôme

- BOUYMEJJANE Badr
- JARROUD Oussama

### Encadrant

- HESSANE Abdelaaziz