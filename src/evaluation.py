from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def mean_absolute_percentage_error_safe(
    y_true: Iterable[float],
    y_pred: Iterable[float],
    epsilon: float = 1e-8,
) -> float:
    """
    Calcule le MAPE en évitant la division par zéro.
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    denominator = np.maximum(np.abs(y_true_arr), epsilon)
    return float(np.mean(np.abs((y_true_arr - y_pred_arr) / denominator)) * 100)

def regression_metrics(
    y_true: Iterable[float],
    y_pred: Iterable[float],
    model_name: str = "model",
) -> Dict[str, float | str]:
    """
    Calcule MAE, RMSE, MAPE et R².
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    mae = mean_absolute_error(y_true_arr, y_pred_arr)
    rmse = np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))
    mape = mean_absolute_percentage_error_safe(y_true_arr, y_pred_arr)
    r2 = r2_score(y_true_arr, y_pred_arr)

    return {
        "model": model_name,
        "MAE": float(mae),
        "RMSE": float(rmse),
        "MAPE": float(mape),
        "R2": float(r2),
    }

def compare_models(metrics: List[Dict[str, float | str]]) -> pd.DataFrame:
    """
    Construit un tableau comparatif trié par MAPE.
    """
    table = pd.DataFrame(metrics)
    return table.sort_values("MAPE").reset_index(drop=True)

def plot_actual_vs_predicted(
    y_true: pd.Series,
    y_pred: Iterable[float],
    title: str = "Réel vs prédit",
    save_path: str | Path | None = None,
) -> None:
    """
    Trace la série réelle et la série prédite.
    """
    prediction = pd.Series(y_pred, index=y_true.index, name="prediction")

    plt.figure(figsize=(14, 5))
    plt.plot(y_true.index, y_true.values, label="Réel", linewidth=1.2)
    plt.plot(prediction.index, prediction.values, label="Prédit", linewidth=1.2)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Charge")
    plt.legend()
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)

    plt.show()

def error_by_hour(
    y_true: pd.Series,
    y_pred: Iterable[float],
) -> pd.DataFrame:
    """
    Calcule les erreurs absolues moyennes par heure de la journée.
    """
    pred = pd.Series(y_pred, index=y_true.index)
    errors = (y_true - pred).abs()

    result = pd.DataFrame({"absolute_error": errors})
    result["hour"] = result.index.hour

    return result.groupby("hour")["absolute_error"].agg(["mean", "median", "max"])

def error_by_dayofweek(
    y_true: pd.Series,
    y_pred: Iterable[float],
) -> pd.DataFrame:
    """
    Calcule les erreurs absolues moyennes par jour de semaine.
    """
    pred = pd.Series(y_pred, index=y_true.index)
    errors = (y_true - pred).abs()

    result = pd.DataFrame({"absolute_error": errors})
    result["dayofweek"] = result.index.dayofweek

    return result.groupby("dayofweek")["absolute_error"].agg(["mean", "median", "max"])

def peak_load_metrics(
    y_true: pd.Series,
    y_pred: Iterable[float],
    percentile: float = 0.90,
    model_name: str = "model_peak",
) -> Dict[str, float | str]:
    """
    Calcule les métriques uniquement pour les charges au-dessus du `percentile`.
    """
    threshold = y_true.quantile(percentile)
    mask = y_true >= threshold
    
    y_true_peak = y_true[mask]
    y_pred_peak = pd.Series(y_pred, index=y_true.index)[mask]
    
    return regression_metrics(y_true_peak, y_pred_peak, model_name=model_name)

def simulate_heatwave(
    X_test: pd.DataFrame,
    temperature_increase: float = 3.0,
    temp_col: str = "temperature",
) -> pd.DataFrame:
    """
    Augmente la température pour simuler une vague de chaleur.
    Retourne un nouveau DataFrame.
    """
    X_simulated = X_test.copy()
    if temp_col in X_simulated.columns:
        X_simulated[temp_col] += temperature_increase
    return X_simulated

def evaluate_degradation(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    y_pred_global: pd.Series,
    is_weekend_col: str = "is_weekend",
    month_col: str = "month",
    predict_func=None,
) -> pd.DataFrame:
    """
    Calcule les métriques globales et par sous-ensembles (Canicule, Pics, Week-end, Été).
    Retourne un DataFrame comparatif.
    """
    results = []
    
    # 1. Global
    metrics_global = regression_metrics(y_test, y_pred_global, model_name="Test complet")
    results.append(metrics_global)
    global_mape = metrics_global["MAPE"]
    
    # 2. Vague de chaleur (+5°C)
    if predict_func is not None:
        X_heatwave = simulate_heatwave(X_test, temperature_increase=5.0)
        y_pred_heatwave = predict_func(model, X_heatwave)
        metrics_heatwave = regression_metrics(y_test, y_pred_heatwave, model_name="Température élevée (+5°C)")
        results.append(metrics_heatwave)
        
    # 3. Forte charge (>= 90e percentile)
    metrics_peak = peak_load_metrics(y_test, y_pred_global, percentile=0.90, model_name="Forte charge (>= P90)")
    results.append(metrics_peak)
    
    # 4. Week-end
    if is_weekend_col in X_test.columns:
        mask_we = X_test[is_weekend_col] == 1
        if mask_we.any():
            metrics_we = regression_metrics(y_test[mask_we], y_pred_global[mask_we], model_name="Week-end")
            results.append(metrics_we)
            
    # 5. Été (Juin, Juillet, Août : mois 6, 7, 8)
    if month_col in X_test.columns:
        mask_summer = X_test[month_col].isin([6, 7, 8])
        if mask_summer.any():
            metrics_summer = regression_metrics(y_test[mask_summer], y_pred_global[mask_summer], model_name="Été")
            results.append(metrics_summer)
            
    df_results = pd.DataFrame(results)
    
    # Calcul de la dégradation
    df_results["Dégradation vs global"] = df_results["MAPE"].apply(
        lambda x: f"{(x - global_mape):+.2f}%" if pd.notnull(x) else ""
    )
    
    # On met la référence à vide ou "Réf"
    if len(df_results) > 0:
        df_results.loc[0, "Dégradation vs global"] = "Référence"
        
    return df_results
