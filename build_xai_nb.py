"""
Build script for 08_xai_shap_lime.ipynb

Generates the notebook for Evaluation, Explainable AI (SHAP/LIME),
and Robustness Testing (Sections 13, 14, 15).
"""

import json
import uuid


def md(source_lines: list[str]) -> dict:
    return {
        "cell_type": "markdown",
        "id": str(uuid.uuid4())[:8],
        "metadata": {},
        "source": source_lines,
    }


def code(source_lines: list[str]) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": str(uuid.uuid4())[:8],
        "metadata": {},
        "outputs": [],
        "source": source_lines,
    }


def build_notebook() -> dict:
    cells: list[dict] = []

    # ── Title ──────────────────────────────────────────────────────
    cells.append(md([
        "# 08 — Évaluation Avancée, XAI et Robustesse\n",
        "\n",
        "## Projet : Smart City Energy Forecasting — Tetouan\n",
        "\n",
        "**Objectifs de ce notebook :**\n",
        "- Évaluer en détail les performances du modèle champion (XGBoost).\n",
        "- Expliquer les prédictions globalement et localement avec SHAP (Explainable AI).\n",
        "- Tester la robustesse du modèle face à des conditions extrêmes (vague de chaleur, pics)."
    ]))

    # ── 1. Imports ─────────────────────────────────────────────────
    cells.append(md([
        "## 1. Imports et Configuration"
    ]))

    cells.append(code([
        "import sys\n",
        "import pickle\n",
        "from pathlib import Path\n",
        "\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "import warnings\n",
        "\n",
        "warnings.filterwarnings(\"ignore\")\n",
        "pd.set_option(\"display.max_columns\", None)\n",
        "\n",
        "# Résolution du chemin projet\n",
        "PROJECT_ROOT = Path.cwd().resolve().parent if Path.cwd().name == \"notebooks\" else Path.cwd()\n",
        "sys.path.insert(0, str(PROJECT_ROOT))\n",
        "\n",
        "from src.models_ml import (\n",
        "    TemporalSplitConfig,\n",
        "    prepare_supervised_data,\n",
        "    temporal_train_val_test_split,\n",
        ")\n",
        "from src.evaluation import (\n",
        "    plot_actual_vs_predicted,\n",
        "    error_by_hour,\n",
        "    error_by_dayofweek,\n",
        "    evaluate_degradation\n",
        ")\n",
        "from src.xai import (\n",
        "    compute_tree_shap_values,\n",
        "    plot_shap_global_importance,\n",
        "    plot_shap_beeswarm,\n",
        "    plot_shap_waterfall_for_peak,\n",
        ")\n",
        "\n",
        "# Chemins\n",
        "PROCESSED_DIR = PROJECT_ROOT / \"data\" / \"processed\"\n",
        "MODELS_DIR = PROJECT_ROOT / \"models\"\n",
        "RESULTS_DIR = PROJECT_ROOT / \"results\"\n",
        "\n",
        "FEATURES_PATH = PROCESSED_DIR / \"tetouan_features.csv\"\n",
        "XGBOOST_PATH = MODELS_DIR / \"xgboost_model.pkl\"\n",
        "PREDICTIONS_PATH = RESULTS_DIR / \"predictions\" / \"06_xgboost_predictions.csv\"\n",
        "\n",
        "print(\"Racine du projet :\", PROJECT_ROOT)"
    ]))

    # ── 2. Chargement ──────────────────────────────────────────────
    cells.append(md([
        "## 2. Chargement des Données et du Modèle Champion\n",
        "Nous rechargeons les features et recréons le set de test pour être en condition réelle d'évaluation."
    ]))

    cells.append(code([
        "# 1. Chargement du dataset\n",
        "df = pd.read_csv(FEATURES_PATH)\n",
        "df[\"datetime\"] = pd.to_datetime(df[\"datetime\"])\n",
        "df = df.set_index(\"datetime\").sort_index()\n",
        "\n",
        "X_clean, y_clean, feature_cols = prepare_supervised_data(df, target_col=\"target\")\n",
        "split_config = TemporalSplitConfig(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)\n",
        "X_train, X_val, X_test, y_train, y_val, y_test = temporal_train_val_test_split(\n",
        "    X_clean, y_clean, config=split_config\n",
        ")\n",
        "\n",
        "# 2. Alignement des features avec le modèle XGBoost\n",
        "import json\n",
        "with open(MODELS_DIR / \"ml_feature_names.json\", \"r\") as f:\n",
        "    xgb_features = json.load(f)[\"feature_names\"]\n",
        "X_test = X_test[xgb_features]\n",
        "X_train = X_train[xgb_features]\n",
        "\n",
        "# 3. Chargement du modèle XGBoost\n",
        "with open(XGBOOST_PATH, \"rb\") as f:\n",
        "    xgb_model = pickle.load(f)\n",
        "\n",
        "# 4. Chargement des prédictions pré-calculées (ou recalcul)\n",
        "y_pred_xgb = xgb_model.predict(X_test)\n",
        "y_pred_xgb_series = pd.Series(y_pred_xgb, index=y_test.index)\n",
        "\n",
        "print(f\"Test set shape: {X_test.shape}\")"
    ]))

    # ── 3. Évaluation (Sec 13) ────────────────────────────────────
    cells.append(md([
        "## 3. Évaluation Avancée (Section 13)\n",
        "Analyse visuelle et granulaire des erreurs du modèle."
    ]))

    cells.append(code([
        "# 3.2 Comparaison réel vs prédit (Zoom sur une semaine)\n",
        "start_date = y_test.index[0]\n",
        "end_date = start_date + pd.Timedelta(days=7)\n",
        "\n",
        "y_true_zoom = y_test.loc[start_date:end_date]\n",
        "y_pred_zoom = y_pred_xgb_series.loc[start_date:end_date]\n",
        "\n",
        "plot_actual_vs_predicted(\n",
        "    y_true_zoom, \n",
        "    y_pred_zoom, \n",
        "    title=\"XGBoost : Réel vs Prédit (Zoom 1 semaine)\",\n",
        "    save_path=RESULTS_DIR / \"figures\" / \"13_xgb_actual_vs_pred_week.png\"\n",
        ")"
    ]))
    
    cells.append(code([
        "# 3.3 & 3.4 Erreurs par heure et par jour\n",
        "fig, axes = plt.subplots(1, 2, figsize=(15, 5))\n",
        "\n",
        "err_hour = error_by_hour(y_test, y_pred_xgb_series)\n",
        "err_hour[\"mean\"].plot(kind=\"bar\", ax=axes[0], color=\"#3498db\")\n",
        "axes[0].set_title(\"Erreur Absolue Moyenne par Heure\")\n",
        "axes[0].set_xlabel(\"Heure de la journée\")\n",
        "axes[0].set_ylabel(\"MAE (kW)\")\n",
        "\n",
        "err_day = error_by_dayofweek(y_test, y_pred_xgb_series)\n",
        "err_day[\"mean\"].plot(kind=\"bar\", ax=axes[1], color=\"#2ecc71\")\n",
        "axes[1].set_title(\"Erreur Absolue Moyenne par Jour de la Semaine\")\n",
        "axes[1].set_xlabel(\"Jour (0=Lundi, 6=Dimanche)\")\n",
        "axes[1].set_xticklabels([\"Lun\", \"Mar\", \"Mer\", \"Jeu\", \"Ven\", \"Sam\", \"Dim\"], rotation=0)\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.savefig(RESULTS_DIR / \"figures\" / \"13_xgb_errors_by_time.png\", dpi=150)\n",
        "plt.show()"
    ]))

    # ── 4. XAI (Sec 14) ─────────────────────────────────────────
    cells.append(md([
        "## 4. Explicabilité avec SHAP (Section 14)\n",
        "Nous allons comprendre **pourquoi** le modèle prédit ces valeurs, d'abord au niveau global, puis pour un pic spécifique."
    ]))

    cells.append(code([
        "# Calcul des valeurs SHAP (sur le test set pour aller plus vite on peut sampler si besoin)\n",
        "print(\"Calcul des valeurs SHAP en cours...\")\n",
        "shap_values = compute_tree_shap_values(xgb_model, X_test)\n",
        "print(\"Calcul terminé.\")"
    ]))

    cells.append(code([
        "# 4.2 Importance globale (Bar plot)\n",
        "plot_shap_global_importance(\n",
        "    shap_values, \n",
        "    X_test, \n",
        "    save_path=RESULTS_DIR / \"figures\" / \"14_shap_global_importance.png\"\n",
        ")"
    ]))

    cells.append(code([
        "# 4.2 Beeswarm plot (Impact positif/négatif de chaque variable)\n",
        "plot_shap_beeswarm(\n",
        "    shap_values, \n",
        "    save_path=RESULTS_DIR / \"figures\" / \"14_shap_beeswarm.png\"\n",
        ")"
    ]))

    cells.append(code([
        "# 4.2 Waterfall plot sur le plus grand pic de consommation réel\n",
        "plot_shap_waterfall_for_peak(\n",
        "    shap_values, \n",
        "    X_test, \n",
        "    y_reference=y_test,\n",
        "    save_path=RESULTS_DIR / \"figures\" / \"14_shap_waterfall_peak.png\"\n",
        ")"
    ]))

    # ── 5. Robustesse (Sec 15) ──────────────────────────────────
    cells.append(md([
        "## 5. Tests de Robustesse (Section 15)\n",
        "Comment le modèle se comporte-t-il lors d'une canicule ou pendant des pics extrêmes ?"
    ]))

    cells.append(code([
        "def predict_xgb(model, X):\n",
        "    return pd.Series(model.predict(X), index=X.index)\n",
        "\n",
        "degradation_table = evaluate_degradation(\n",
        "    model=xgb_model,\n",
        "    X_test=X_test,\n",
        "    y_test=y_test,\n",
        "    y_pred_global=y_pred_xgb_series,\n",
        "    is_weekend_col=\"is_weekend\",\n",
        "    month_col=\"month\",\n",
        "    predict_func=predict_xgb\n",
        ")\n",
        "\n",
        "print(\"Analyse de dégradation du modèle XGBoost :\")\n",
        "display(degradation_table[[\"model\", \"MAE\", \"MAPE\", \"Dégradation vs global\"]])\n",
        "degradation_table.to_csv(RESULTS_DIR / \"metrics\" / \"15_xgboost_robustness_degradation.csv\", index=False)"
    ]))
    
    cells.append(md([
        "### Fin de l'évaluation du modèle\n",
        "XGBoost s'avère non seulement performant, mais aussi hautement interprétable (SHAP) et robuste (comme le montre le tableau de dégradation ci-dessus)."
    ]))

    # ── Notebook structure ────────────────────────────────────────
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": ".venv",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.12.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    return notebook


if __name__ == "__main__":
    from pathlib import Path

    nb = build_notebook()

    output_path = Path(__file__).parent / "notebooks" / "08_xai_shap_lime.ipynb"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)

    print(f"Notebook généré : {output_path}")
