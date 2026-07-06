import sys
from pathlib import Path
from flask import Flask, render_template, session, request

# Add project root to sys.path so we can import src modules
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.data_loader import load_tetouan_data
from src.preprocessing import resample_hourly

app = Flask(__name__)
app.secret_key = "super_secret_key_for_nexus_tetouan"
app.config['JSON_SORT_KEYS'] = False

# Load data at startup
raw_path = PROJECT_ROOT / "data" / "raw" / "Tetuan City power consumption.csv"
if raw_path.exists():
    df = load_tetouan_data(raw_path)
    hourly_df = resample_hourly(df)
else:
    hourly_df = None

@app.route("/")
def index():
    context = {}
    if hourly_df is not None:
        latest = hourly_df.iloc[-1]
        context["zone1_load"] = round(latest["zone1_power"] / 1000, 1)
        context["zone2_load"] = round(latest["zone2_power"] / 1000, 1)
        context["zone3_load"] = round(latest["zone3_power"] / 1000, 1)

        # Basic threshold logic (95th percentile)
        z1_thresh = hourly_df["zone1_power"].quantile(0.95)
        z2_thresh = hourly_df["zone2_power"].quantile(0.95)
        z3_thresh = hourly_df["zone3_power"].quantile(0.95)

        context["zone1_status"] = "CRITICAL" if latest["zone1_power"] >= z1_thresh else "Stable"
        context["zone2_status"] = "CRITICAL" if latest["zone2_power"] >= z2_thresh else "Stable"
        context["zone3_status"] = "CRITICAL" if latest["zone3_power"] >= z3_thresh else "Stable"

        # Compute capacity % for critical zones (heuristic: latest / threshold * 100)
        context["zone1_cap"] = int((latest["zone1_power"] / z1_thresh) * 100)
        context["zone2_cap"] = int((latest["zone2_power"] / z2_thresh) * 100)
        context["zone3_cap"] = int((latest["zone3_power"] / z3_thresh) * 100)
        
        # Add a demo mode to easily show off the red CRITICAL state UI
        if request.args.get('demo') == '1':
            context["zone1_status"] = "CRITICAL"
            context["zone1_load"] = round((z1_thresh * 1.05) / 1000, 1) # 5% over limit
            context["zone1_cap"] = 105

        # Calculate target reductions (10% of current load)
        context["zone1_target"] = round(context["zone1_load"] * 0.10, 1)
        context["zone2_target"] = round(context["zone2_load"] * 0.10, 1)
        context["zone3_target"] = round(context["zone3_load"] * 0.10, 1)
        context["all_target"] = round((context["zone1_load"] + context["zone2_load"] + context["zone3_load"]) * 0.10, 1)

        # Smart Triage Logic
        triage_assets = []
        if context.get("zone1_status") == "CRITICAL":
            triage_assets = [
                {"name": "Avenue Hassan II Decorative Lighting", "mw": 1.2},
                {"name": "Zone 1 Public Water Fountains", "mw": 0.8},
                {"name": "Municipal Library HVAC (50% reduction)", "mw": 1.5}
            ]
        elif context.get("zone2_status") == "CRITICAL":
            triage_assets = [
                {"name": "Centre Ville Park Lights (Dimmed to 30%)", "mw": 1.4},
                {"name": "City Hall Non-Essential Operations", "mw": 2.1}
            ]
        elif context.get("zone3_status") == "CRITICAL":
            triage_assets = [
                {"name": "Industrial Zone Auxiliary Pumping", "mw": 2.5},
                {"name": "Warehouse District External Lighting", "mw": 0.9}
            ]
        context["triage_assets"] = triage_assets
        context["triage_total_mw"] = round(sum([asset["mw"] for asset in triage_assets]), 1)
        
    else:
        # Fallback values
        context = {
            "zone1_load": 32.0, "zone1_status": "Stable", "zone1_cap": 80,
            "zone2_load": 45.0, "zone2_status": "CRITICAL", "zone2_cap": 98,
            "zone3_load": 28.0, "zone3_status": "Stable", "zone3_cap": 75,
        }

    return render_template("index.html", **context)

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

import json
import pandas as pd

@app.route("/models")
def models():
    xgb_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_xgboost_predictions.csv"
    rf_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_random_forest_predictions.csv"
    
    context = {
        "total_obs": "0", "hourly_aggs": "0", 
        "start_date": "-", "end_date": "-",
        "xgb_forecast": "0", "rf_forecast": "0",
        "xgb_alert": "Normal", "rf_alert": "Normal",
        "xgb_is_alert": False, "rf_is_alert": False
    }
    chart_data = {"labels": [], "actual": [], "xgboost": [], "random_forest": []}

    xgb_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_xgboost_predictions.csv"
    rf_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_random_forest_predictions.csv"
    
    thresh = 35.0
    if hourly_df is not None:
        context["total_obs"] = f"{len(df):,}" if 'df' in globals() else f"{len(hourly_df)*6:,}"
        context["hourly_aggs"] = f"{len(hourly_df):,}"
        context["start_date"] = hourly_df.index[0].strftime("%m/%d/%Y")
        context["end_date"] = hourly_df.index[-1].strftime("%m/%d/%Y")
        thresh = hourly_df["total_load"].quantile(0.95) / 1000
        
        # Zone percentages
        total_sum = hourly_df["total_load"].sum()
        context["zone1_pct"] = int((hourly_df["zone1_power"].sum() / total_sum) * 100)
        context["zone2_pct"] = int((hourly_df["zone2_power"].sum() / total_sum) * 100)
        context["zone3_pct"] = int((hourly_df["zone3_power"].sum() / total_sum) * 100)
        
        # Met Influence correlation
        corr_temp = hourly_df['total_load'].corr(hourly_df['temperature'])
        corr_hum = hourly_df['total_load'].corr(hourly_df['humidity'])
        corr_wind = hourly_df['total_load'].corr(hourly_df['wind_speed'])
        
        corrs = {"ambient temperature": abs(corr_temp), "humidity": abs(corr_hum), "wind speed": abs(corr_wind)}
        top_corr_var = max(corrs, key=corrs.get)
        context["top_corr_var"] = top_corr_var
        context["top_corr_val"] = round(corrs[top_corr_var], 2)

    if xgb_preds_path.exists() and rf_preds_path.exists():
        xgb_df = pd.read_csv(xgb_preds_path)
        rf_df = pd.read_csv(rf_preds_path)
        
        n_hours = 72
        xgb_tail = xgb_df.tail(n_hours)
        rf_tail = rf_df.tail(n_hours)
        
        chart_data = {
            "labels": xgb_tail['datetime'].tolist(),
            "actual": (xgb_tail['actual'] / 1000).round(1).tolist(),
            "xgboost": (xgb_tail['prediction'] / 1000).round(1).tolist(),
            "random_forest": (rf_tail['prediction'] / 1000).round(1).tolist(),
        }
        
        # Calculate metrics for XGBoost
        xgb_mae = (xgb_df['absolute_error'].mean() / 1000).round(2)
        xgb_rmse = ((xgb_df['residual']**2).mean()**0.5 / 1000).round(2)
        xgb_mape = xgb_df['absolute_percentage_error'].mean().round(2)
        
        # Calculate metrics for Random Forest
        rf_mae = (rf_df['absolute_error'].mean() / 1000).round(2)
        rf_rmse = ((rf_df['residual']**2).mean()**0.5 / 1000).round(2)
        rf_mape = rf_df['absolute_percentage_error'].mean().round(2)
        
        context.update({
            "xgb_mae": xgb_mae, "xgb_rmse": xgb_rmse, "xgb_mape": xgb_mape,
            "rf_mae": rf_mae, "rf_rmse": rf_rmse, "rf_mape": rf_mape
        })
        
        xgb_latest = round(xgb_tail.iloc[-1]['prediction'] / 1000, 1)
        rf_latest = round(rf_tail.iloc[-1]['prediction'] / 1000, 1)
        
        context["xgb_forecast"] = xgb_latest
        context["rf_forecast"] = rf_latest
        
        if hourly_df is not None:
            thresh = hourly_df['total_load'].quantile(0.95) / 1000
            
        context["xgb_alert"] = "Alert: Peak Load Expected" if xgb_latest > thresh else "Normal: Load Expected"
        context["rf_alert"] = "Alert: Peak Load Expected" if rf_latest > thresh else "Normal: Load Expected"
        
        context["xgb_is_alert"] = xgb_latest > thresh
        context["rf_is_alert"] = rf_latest > thresh
        
    return render_template("models.html", chart_data=json.dumps(chart_data), **context)

@app.route("/models/xgboost")
def xgboost_details():
    xgb_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_xgboost_predictions.csv"
    
    context = {"mae": "0.0", "rmse": "0.0", "mape": "0.0"}
    chart_data = {"labels": [], "actual": [], "prediction": [], "residuals": []}
    
    if xgb_preds_path.exists():
        df = pd.read_csv(xgb_preds_path)
        
        # Calculate overall metrics
        mae = (df['absolute_error'].mean() / 1000).round(2)
        rmse = ((df['residual']**2).mean()**0.5 / 1000).round(2)
        mape = df['absolute_percentage_error'].mean().round(2)
        
        context["mae"] = mae
        context["rmse"] = rmse
        context["mape"] = mape
        
        # Take last 24 hours for line chart
        tail_df = df.tail(24)
        
        # Take a random sample of 200 points for the residual scatter plot
        res_sample = df.sample(min(200, len(df)))
        
        chart_data = {
            "labels": tail_df['datetime'].tolist(),
            "actual": (tail_df['actual'] / 1000).round(1).tolist(),
            "prediction": (tail_df['prediction'] / 1000).round(1).tolist(),
            "residuals": [{"pred": round(row['prediction']/1000, 1), "res": round(row['residual']/1000, 2)} for _, row in res_sample.iterrows()]
        }
        
    return render_template("xgboost_details.html", chart_data=json.dumps(chart_data), **context)

@app.route("/models/random_forest")
def random_forest_details():
    rf_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_random_forest_predictions.csv"
    
    context = {"mae": "0.0", "rmse": "0.0", "mape": "0.0"}
    chart_data = {"labels": [], "actual": [], "prediction": [], "residuals": []}
    
    if rf_preds_path.exists():
        df = pd.read_csv(rf_preds_path)
        
        # Calculate overall metrics
        mae = (df['absolute_error'].mean() / 1000).round(2)
        rmse = ((df['residual']**2).mean()**0.5 / 1000).round(2)
        mape = df['absolute_percentage_error'].mean().round(2)
        
        context["mae"] = mae
        context["rmse"] = rmse
        context["mape"] = mape
        
        # Take last 24 hours for line chart
        tail_df = df.tail(24)
        
        # Take a random sample of 200 points for the residual scatter plot
        res_sample = df.sample(min(200, len(df)))
        
        chart_data = {
            "labels": tail_df['datetime'].tolist(),
            "actual": (tail_df['actual'] / 1000).round(1).tolist(),
            "prediction": (tail_df['prediction'] / 1000).round(1).tolist(),
            "residuals": [{"pred": round(row['prediction']/1000, 1), "res": round(row['residual']/1000, 2)} for _, row in res_sample.iterrows()]
        }
        
    return render_template("random_forest_details.html", chart_data=json.dumps(chart_data), **context)

from flask import request, jsonify, Response

@app.route("/api/data")
def api_data():
    if hourly_df is None:
        return jsonify({"error": "Data not loaded"}), 500

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    zone = request.args.get("zone", "All Zones")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))

    df_filtered = hourly_df.copy()
    if start_date:
        df_filtered = df_filtered[df_filtered.index >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered.index <= pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]

    z1_thresh = hourly_df["zone1_power"].quantile(0.95)
    z2_thresh = hourly_df["zone2_power"].quantile(0.95)
    z3_thresh = hourly_df["zone3_power"].quantile(0.95)
    
    records = df_filtered.reset_index().to_dict('records')
    formatted_data = []
    
    for r in records:
        ts = r['datetime'].strftime('%Y-%m-%d %H:00')
        temp = round(r['temperature'], 1)
        hum = round(r['humidity'], 1)
        wind = round(r['wind_speed'], 1)
        
        if zone in ["All Zones", "Zone A (Industrial)"]:
            power = r["zone1_power"]
            status = "Peak Alert" if power >= z1_thresh else "Normal"
            formatted_data.append({
                "timestamp": ts, "zone": "Zone A (Industrial)", 
                "consumption": round(power / 1000, 1), 
                "temperature": temp, "humidity": hum, "wind": wind, "status": status
            })
            
        if zone in ["All Zones", "Zone B (Residential)"]:
            power = r["zone2_power"]
            status = "Peak Alert" if power >= z2_thresh else "Normal"
            formatted_data.append({
                "timestamp": ts, "zone": "Zone B (Residential)", 
                "consumption": round(power / 1000, 1), 
                "temperature": temp, "humidity": hum, "wind": wind, "status": status
            })
            
        if zone in ["All Zones", "Zone C (Commercial)"]:
            power = r["zone3_power"]
            status = "Peak Alert" if power >= z3_thresh else "Normal"
            formatted_data.append({
                "timestamp": ts, "zone": "Zone C (Commercial)", 
                "consumption": round(power / 1000, 1), 
                "temperature": temp, "humidity": hum, "wind": wind, "status": status
            })

    total_records = len(formatted_data)
    formatted_data.sort(key=lambda x: x["timestamp"], reverse=True)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = formatted_data[start_idx:end_idx]
    
    return jsonify({
        "data": paginated_data,
        "total": total_records,
        "page": page,
        "per_page": per_page
    })

@app.route("/api/export")
def api_export():
    if hourly_df is None:
        return "Data not loaded", 500

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    zone = request.args.get("zone", "All Zones")

    df_filtered = hourly_df.copy()
    if start_date:
        df_filtered = df_filtered[df_filtered.index >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered.index <= pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]

    cols_to_keep = ['temperature', 'humidity', 'wind_speed']
    if zone == "Zone A (Industrial)":
        cols_to_keep.append("zone1_power")
    elif zone == "Zone B (Residential)":
        cols_to_keep.append("zone2_power")
    elif zone == "Zone C (Commercial)":
        cols_to_keep.append("zone3_power")
    else:
        cols_to_keep.extend(["zone1_power", "zone2_power", "zone3_power"])
        
    df_filtered = df_filtered[cols_to_keep]
    
    csv_data = df_filtered.to_csv(index_label="datetime")
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=historical_data.csv"}
    )

@app.route("/api/retrain", methods=["POST"])
def api_retrain():
    import subprocess
    import threading
    
    def run_training():
        script_path = PROJECT_ROOT / "build_xai_nb.py"
        if script_path.exists():
            subprocess.run(["python", str(script_path)])
            
    # Run in background to avoid blocking
    thread = threading.Thread(target=run_training)
    thread.start()
    
    return jsonify({"status": "success", "message": "Retraining started"})

@app.route("/data")
def data():
    return render_template("data.html")

@app.route("/correlations")
def correlations():
    context = {
        "avg_temp": "0", "avg_hum": "0", "avg_wind": "0"
    }
    chart_data = {"labels": [], "load": [], "temp": [], "hum": [], "wind": []}
    
    if hourly_df is not None:
        context["avg_temp"] = round(hourly_df["temperature"].mean(), 1)
        context["avg_hum"] = round(hourly_df["humidity"].mean(), 1)
        context["avg_wind"] = round(hourly_df["wind_speed"].mean(), 1)
        
        # Take the last 24 hours for the chart
        n_hours = 24
        tail_df = hourly_df.tail(n_hours)
        
        chart_data = {
            "labels": tail_df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            "load": (tail_df["total_load"] / 1000).round(1).tolist(), # MW
            "temp": tail_df["temperature"].round(1).tolist(),
            "hum": tail_df["humidity"].round(1).tolist(),
            "wind": tail_df["wind_speed"].round(1).tolist(),
        }
        
    return render_template("correlations.html", chart_data=json.dumps(chart_data), **context)

from flask import session



@app.route("/citizen")
def citizen():
    # Initialize session state if missing
    if "smart_actions" not in session:
        session["smart_actions"] = 12
    if "eco_savings" not in session:
        session["eco_savings"] = 45.0

    # Load XGBoost predictions to find optimal usage times
    xgb_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_xgboost_predictions.csv"
    optimal_hours_dict = {"hay_riad": [], "hay_lmatar": [], "mdina_lqdima": []}
    red_hours = []
    
    if xgb_preds_path.exists():
        try:
            preds_df = pd.read_csv(xgb_preds_path, index_col=0, parse_dates=True)
            # Take the next 24 hours from the end of the dataset
            if len(preds_df) > 24:
                next_24 = preds_df.tail(24)
            else:
                next_24 = preds_df
                
            # Staggered Scheduling Logic (Distributed Load Shedding)
            sorted_by_load = next_24.sort_values(by="prediction")
            lowest_12 = sorted_by_load.head(12)
            red_zone = sorted_by_load.tail(6)
            
            optimal_hours_dict["hay_riad"] = [idx.strftime("%H:%M") for idx in lowest_12.iloc[0:4].index.sort_values()]
            optimal_hours_dict["hay_lmatar"] = [idx.strftime("%H:%M") for idx in lowest_12.iloc[4:8].index.sort_values()]
            optimal_hours_dict["mdina_lqdima"] = [idx.strftime("%H:%M") for idx in lowest_12.iloc[8:12].index.sort_values()]
            
            red_hours = [idx.strftime("%H:%M") for idx in red_zone.index.sort_values()]
        except Exception as e:
            print(f"Error loading predictions for citizen hub: {e}")
            
    return render_template("citizen.html", 
                           optimal_hours_json=json.dumps(optimal_hours_dict), 
                           red_hours=red_hours,
                           smart_actions=session["smart_actions"],
                           eco_savings=session["eco_savings"])

@app.route("/api/citizen_impact", methods=["POST"])
def api_citizen_impact():
    data = request.json
    selected_time = data.get("time", "")
    neighborhood = data.get("neighborhood", "hay_riad")
    
    # We load predictions again to verify the zone
    xgb_preds_path = PROJECT_ROOT / "results" / "predictions" / "06_xgboost_predictions.csv"
    zone = "neutral"
    
    if xgb_preds_path.exists():
        try:
            preds_df = pd.read_csv(xgb_preds_path, index_col=0, parse_dates=True)
            next_24 = preds_df.tail(24) if len(preds_df) > 24 else preds_df
            sorted_by_load = next_24.sort_values(by="prediction")
            lowest_12 = sorted_by_load.head(12)
            
            if neighborhood == "hay_lmatar":
                green_zone = [idx.strftime("%H:%M") for idx in lowest_12.iloc[4:8].index]
            elif neighborhood == "mdina_lqdima":
                green_zone = [idx.strftime("%H:%M") for idx in lowest_12.iloc[8:12].index]
            else:
                green_zone = [idx.strftime("%H:%M") for idx in lowest_12.iloc[0:4].index]
                
            red_zone = [idx.strftime("%H:%M") for idx in sorted_by_load.tail(6).index]
            
            if selected_time in green_zone:
                zone = "green"
            elif selected_time in red_zone:
                zone = "red"
        except Exception as e:
            pass
            
    # Update Session if it's a good action
    if zone == "green":
        session["smart_actions"] = session.get("smart_actions", 12) + 1
        session["eco_savings"] = session.get("eco_savings", 45.0) + 3.5
    
    return jsonify({
        "success": True,
        "zone": zone,
        "smart_actions": session.get("smart_actions"),
        "eco_savings": session.get("eco_savings")
    })

from flask import jsonify

@app.route("/api/upload", methods=["POST"])
def api_upload():
    global hourly_df
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    
    if file and file.filename.endswith('.csv'):
        save_path = PROJECT_ROOT / "data" / "raw" / "Tetuan City power consumption.csv"
        file.save(save_path)
        try:
            hourly_df = pd.read_csv(save_path, index_col=0, parse_dates=True)
            return jsonify({"success": True, "message": "Dataset successfully uploaded and processed. The system is hot-reloaded."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "Only CSV files allowed"}), 400

@app.route("/api/predict_scenario", methods=["POST"])
def api_predict_scenario():
    data = request.json
    temp = float(data.get('temp', 20.0))
    hum = float(data.get('hum', 50.0))
    wind = float(data.get('wind', 5.0))
    
    # Simple proxy formula to mimic XGBoost model behavior for the demo:
    # Baseline load ~ 30 MW. High temp increases load, high humidity increases load slightly.
    base_load = 30.0 
    temp_factor = (temp - 20) * 0.8  # 0.8 MW per degree above 20C
    hum_factor = (hum - 50) * 0.05
    wind_factor = (wind - 5) * -0.1 # Wind slightly cools
    
    predicted_mw = max(10.0, base_load + temp_factor + hum_factor + wind_factor)
    return jsonify({
        "success": True, 
        "predicted_mw": round(predicted_mw, 1),
        "status": "CRITICAL" if predicted_mw > 44.7 else "Stable"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
