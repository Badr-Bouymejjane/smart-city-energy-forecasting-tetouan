import json

def get_notebook_structure():
    return {
      "cells": [
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "# 07 — Modélisation Deep Learning : GRU\n",
            "\n",
            "## Projet : Smart City Energy Forecasting — Tetouan\n",
            "\n",
            "Ce notebook correspond à l'étape **Deep Learning** du pipeline KDD.\n",
            "\n",
            "Objectif :\n",
            "- utiliser le dataset déjà enrichi par feature engineering ;\n",
            "- formater les données en séquences 3D temporelles (fenêtre glissante) ;\n",
            "- entraîner un réseau de neurones récurrents GRU (Gated Recurrent Unit) ;\n",
            "- analyser les erreurs par heure, par jour et pendant les fortes charges, tout comme avec XGBoost ;\n",
            "- sauvegarder les modèles, métriques, prédictions et figures.\n",
            "\n",
            "Règles méthodologiques :\n",
            "- split strictement chronologique ;\n",
            "- évaluation globale et métier."
          ]
        },
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "## 1. Importation des bibliothèques et configuration"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "from pathlib import Path\n",
            "import sys\n",
            "import warnings\n",
            "\n",
            "import numpy as np\n",
            "import pandas as pd\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "warnings.filterwarnings(\"ignore\")\n",
            "pd.set_option(\"display.max_columns\", None)\n",
            "pd.set_option(\"display.width\", 160)\n",
            "\n",
            "# Détection automatique de la racine du projet.\n",
            "PROJECT_ROOT = Path.cwd().resolve().parent if Path.cwd().name == \"notebooks\" else Path.cwd().resolve()\n",
            "if str(PROJECT_ROOT) not in sys.path:\n",
            "    sys.path.append(str(PROJECT_ROOT))\n",
            "\n",
            "from src.models_ml import (\n",
            "    set_global_seed,\n",
            "    prepare_supervised_data,\n",
            "    temporal_train_val_test_split,\n",
            "    print_split_summary,\n",
            "    evaluate_by_hour,\n",
            "    evaluate_by_dayofweek,\n",
            "    evaluate_peak_load,\n",
            "    plot_actual_vs_predicted,\n",
            "    plot_error_by_hour,\n",
            "    save_dataframe\n",
            ")\n",
            "\n",
            "from src.models_gru import train_evaluate_gru\n",
            "\n",
            "set_global_seed(42)\n",
            "PROJECT_ROOT"
          ]
        },
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "## 2. Définition des chemins et chargement des données"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "DATA_DIR = PROJECT_ROOT / \"data\"\n",
            "PROCESSED_DIR = DATA_DIR / \"processed\"\n",
            "\n",
            "RESULTS_DIR = PROJECT_ROOT / \"results\"\n",
            "FIGURES_DIR = RESULTS_DIR / \"figures\"\n",
            "METRICS_DIR = RESULTS_DIR / \"metrics\"\n",
            "MODELS_DIR = PROJECT_ROOT / \"models\"\n",
            "\n",
            "for folder in [FIGURES_DIR, METRICS_DIR, MODELS_DIR]:\n",
            "    folder.mkdir(parents=True, exist_ok=True)\n",
            "\n",
            "candidate_feature_paths = [\n",
            "    PROCESSED_DIR / \"tetouan_features.csv\",\n",
            "    PROCESSED_DIR / \"tetouan_features_hourly.csv\",\n",
            "]\n",
            "\n",
            "FEATURES_PATH = next((path for path in candidate_feature_paths if path.exists()), None)\n",
            "if FEATURES_PATH is None:\n",
            "    raise FileNotFoundError(\"Aucun fichier de features trouvé.\")\n",
            "\n",
            "print(\"Fichier de features utilisé :\", FEATURES_PATH)\n",
            "\n",
            "df_features = pd.read_csv(FEATURES_PATH, index_col=0, parse_dates=True)\n",
            "df_features.head()"
          ]
        },
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "## 3. Préparation des données et split temporel"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "X, y, feature_cols = prepare_supervised_data(df_features, target_col=\"target\")\n",
            "X_train, X_val, X_test, y_train, y_val, y_test = temporal_train_val_test_split(X, y)\n",
            "\n",
            "print_split_summary(X_train, X_val, X_test)"
          ]
        },
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "## 4. Entraînement du modèle GRU\n",
            "Nous utilisons un historique de 24 heures (`time_steps = 24`) pour prédire l'heure suivante."
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "time_steps = 24\n",
            "\n",
            "model_gru, metrics_gru, preds_gru, scaler_y = train_evaluate_gru(\n",
            "    X_train, y_train,\n",
            "    X_val, y_val,\n",
            "    X_test, y_test,\n",
            "    time_steps=time_steps,\n",
            "    epochs=30,\n",
            "    batch_size=64\n",
            ")\n",
            "\n",
            "save_dataframe(metrics_gru, METRICS_DIR / \"07_gru_global_metrics.csv\", index=False)\n",
            "metrics_gru"
          ]
        },
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "## 5. Évaluation fine (Heure, Jour de la semaine, Peak Load)"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "# Évaluation par heure de la journée\n",
            "gru_hourly_metrics = evaluate_by_hour(preds_gru)\n",
            "save_dataframe(gru_hourly_metrics, METRICS_DIR / \"07_gru_metrics_by_hour.csv\", index=False)\n",
            "\n",
            "# Plot MAPE par heure\n",
            "fig = plot_error_by_hour(\n",
            "    gru_hourly_metrics,\n",
            "    title=\"GRU — MAPE par heure de la journée\",\n",
            "    metric_col=\"MAPE\",\n",
            "    path=FIGURES_DIR / \"07_gru_mape_by_hour.png\",\n",
            ")\n",
            "plt.show()"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "# Évaluation par jour de la semaine\n",
            "gru_dow_metrics = evaluate_by_dayofweek(preds_gru)\n",
            "save_dataframe(gru_dow_metrics, METRICS_DIR / \"07_gru_metrics_by_dayofweek.csv\", index=False)\n",
            "gru_dow_metrics"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "# Évaluation sur les fortes charges (Top 10%)\n",
            "gru_peak_metrics = evaluate_peak_load(preds_gru, quantile=0.90)\n",
            "gru_peak_df = pd.DataFrame([gru_peak_metrics])\n",
            "gru_peak_df.insert(0, \"Model\", \"GRU\")\n",
            "save_dataframe(gru_peak_df, METRICS_DIR / \"07_gru_peak_load_metrics.csv\", index=False)\n",
            "gru_peak_df"
          ]
        },
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "## 6. Visualisation Global Réel vs Prédit"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "plot_actual_vs_predicted(\n",
            "    pred_df=preds_gru,\n",
            "    title=\"GRU : Réel vs Prédit (300 dernières heures)\",\n",
            "    max_points=300,\n",
            "    path=FIGURES_DIR / \"07_gru_actual_vs_predicted.png\"\n",
            ")"
          ]
        },
        {
          "cell_type": "markdown",
          "metadata": {},
          "source": [
            "## 7. Sauvegarde du modèle"
          ]
        },
        {
          "cell_type": "code",
          "execution_count": None,
          "metadata": {},
          "outputs": [],
          "source": [
            "model_gru.save(MODELS_DIR / \"gru_model.h5\")\n",
            "print(\"Modèle GRU sauvegardé avec succès dans :\", MODELS_DIR / \"gru_model.h5\")"
          ]
        }
      ],
      "metadata": {
        "kernelspec": {
          "display_name": "Python 3",
          "language": "python",
          "name": "python3"
        },
        "language_info": {
          "codemirror_mode": {
            "name": "ipython",
            "version": 3
          },
          "file_extension": ".py",
          "mimetype": "text/x-python",
          "name": "python",
          "nbconvert_exporter": "python",
          "pygments_lexer": "ipython3",
          "version": "3.10.0"
        }
      },
      "nbformat": 4,
      "nbformat_minor": 5
    }

if __name__ == "__main__":
    nb = get_notebook_structure()
    with open("c:/Users/jarro/OneDrive/Desktop/smart-city-energy-forecasting-tetouan/notebooks/07_modeling_gru.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
    print("Notebook 07_modeling_gru.ipynb re-generated successfully!")
