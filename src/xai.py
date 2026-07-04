from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

def compute_tree_shap_values(model, X_sample: pd.DataFrame):
    """
    Calcule les valeurs SHAP pour un modèle d'arbres.

    Compatible avec Random Forest et XGBoost dans la plupart des cas.
    """
    try:
        import shap
    except ImportError as exc:
        raise ImportError("shap n'est pas installé. Exécuter : pip install shap") from exc

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)
    return shap_values

def plot_shap_global_importance(
    shap_values,
    X_sample: pd.DataFrame,
    save_path: str | Path | None = "results/figures/shap_global_importance.png",
) -> None:
    """
    Produit le bar plot d'importance globale SHAP.
    """
    import shap

    shap.plots.bar(shap_values, show=False)
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    plt.show()

def plot_shap_beeswarm(
    shap_values,
    save_path: str | Path | None = "results/figures/shap_beeswarm.png",
) -> None:
    """
    Produit le beeswarm plot SHAP.
    """
    import shap

    shap.plots.beeswarm(shap_values, show=False)
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    plt.show()

def plot_shap_waterfall_for_peak(
    shap_values,
    X_sample: pd.DataFrame,
    y_reference: Optional[pd.Series] = None,
    save_path: str | Path | None = "results/figures/shap_waterfall_peak.png",
) -> None:
    """
    Produit un waterfall plot pour une observation de pic.

    Si y_reference est fourni, l'observation avec la valeur réelle la plus élevée
    est choisie. Sinon, la dernière observation de X_sample est utilisée.
    """
    import shap

    if y_reference is not None:
        selected_index = y_reference.loc[X_sample.index].idxmax()
        position = list(X_sample.index).index(selected_index)
    else:
        position = len(X_sample) - 1

    shap.plots.waterfall(shap_values[position], show=False)
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    plt.show()

def explain_lime_tabular(
    model,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_reference: Optional[pd.Series] = None,
    mode: str = "regression",
) -> None:
    """
    Explique une prédiction avec LIME (local interpretable model-agnostic explanations).
    """
    try:
        import lime
        import lime.lime_tabular
    except ImportError as exc:
        raise ImportError("lime n'est pas installé. Exécuter : pip install lime") from exc

    explainer = lime.lime_tabular.LimeTabularExplainer(
        X_train.values,
        feature_names=X_train.columns.tolist(),
        class_names=["target"],
        mode=mode,
        verbose=True,
    )
    
    if y_reference is not None:
        selected_index = y_reference.loc[X_test.index].idxmax()
        position = list(X_test.index).index(selected_index)
    else:
        position = len(X_test) - 1
        
    exp = explainer.explain_instance(
        X_test.values[position], 
        model.predict, 
        num_features=10
    )
    
    exp.show_in_notebook(show_table=True)
