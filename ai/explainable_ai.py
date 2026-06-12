# ai/explainable_ai.py
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for web servers
import matplotlib.pyplot as plt
import shap
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from database import supabase_client

# Define static directories for plots
STATIC_IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images')
os.makedirs(STATIC_IMG_DIR, exist_ok=True)

# ==========================================
# 1. TRAFFIC CONGESTION ML MODEL
# ==========================================
def train_traffic_model():
    """
    Fetches traffic data from Supabase, fits a RandomForestClassifier,
    and returns (model, feature_names, X_train_dataframe).
    Generates synthetic data if Supabase lacks sufficient records.
    """
    # Try fetching from Supabase
    db_records = supabase_client.get_all_traffic_data()
    
    # If insufficient records, generate a realistic synthetic dataset
    if len(db_records) < 15:
        print("[XAI Traffic] Insufficient database records. Generating synthetic training data...")
        np.random.seed(42)
        n_samples = 150
        
        vehicle_count = np.random.randint(10, 250, n_samples)
        avg_speed = 60.0 - (vehicle_count * 0.18) - np.random.normal(0, 5, n_samples)
        avg_speed = np.clip(avg_speed, 5.0, 80.0)
        
        hour = np.random.randint(0, 24, n_samples)
        is_weekend = np.random.randint(0, 2, n_samples)
        
        # Determine congestion level based on a mathematical relation
        # Low = 0, Medium = 1, High = 2
        congestion_scores = (vehicle_count * 0.4) - (avg_speed * 0.8) + (is_weekend * -5.0)
        congestion_levels = []
        for score in congestion_scores:
            if score < -10:
                congestion_levels.append(0)  # Low
            elif score < 25:
                congestion_levels.append(1)  # Medium
            else:
                congestion_levels.append(2)  # High
                
        df = pd.DataFrame({
            'vehicle_count': vehicle_count,
            'avg_speed': avg_speed,
            'hour': hour,
            'is_weekend': is_weekend,
            'target': congestion_levels
        })
    else:
        # Build dataset from database records
        # Extract features and map labels
        data_list = []
        for r in db_records:
            # Parse timestamp to extract hour and weekday
            ts = pd.to_datetime(r.get('timestamp'))
            hour = ts.hour
            is_weekend = 1 if ts.weekday() >= 5 else 0
            
            cong_map = {'Low': 0, 'Medium': 1, 'High': 2}
            level = cong_map.get(r.get('congestion_level'), 1)
            
            data_list.append({
                'vehicle_count': r.get('vehicle_count'),
                'avg_speed': float(r.get('avg_speed')),
                'hour': hour,
                'is_weekend': is_weekend,
                'target': level
            })
        df = pd.DataFrame(data_list)
        
    feature_cols = ['vehicle_count', 'avg_speed', 'hour', 'is_weekend']
    X = df[feature_cols]
    y = df['target']
    
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    return model, feature_cols, X

def get_traffic_explanation(vehicle_count, avg_speed, hour=12, is_weekend=0):
    """
    Predicts congestion risk (Low/Medium/High) and generates SHAP values.
    """
    model, features, X_train = train_traffic_model()
    
    # Input vector for prediction
    input_data = pd.DataFrame([[vehicle_count, avg_speed, hour, is_weekend]], columns=features)
    
    # Predict probabilities and final class
    prob = model.predict_proba(input_data)[0]
    pred_class_idx = int(np.argmax(prob))
    classes = ['Low', 'Medium', 'High']
    prediction = classes[pred_class_idx]
    
    # SHAP Explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(input_data)
    
    # For multiclass, shap_values is a list of arrays (one per class).
    # We explain the prediction for the predicted class.
    class_shap = shap_values[pred_class_idx][0]
    
    # Standardize output for frontend consumption
    contributions = []
    feature_labels = {
        'vehicle_count': 'Vehicle Density',
        'avg_speed': 'Average Speed (km/h)',
        'hour': 'Hour of Day',
        'is_weekend': 'Weekend Factor'
    }
    
    for feat, val in zip(features, class_shap):
        contributions.append({
            "feature": feat,
            "display_name": feature_labels.get(feat, feat),
            "value": float(input_data[feat].iloc[0]),
            "shap_value": float(val),
            "effect": "Increases Congestion" if val > 0 else "Decreases Congestion"
        })
        
    # Generate SHAP Summary Plot image for traffic model
    try:
        plt.figure(figsize=(6, 4))
        # Summary plot of the full explainer output
        shap_values_full = explainer.shap_values(X_train)
        # Use shap values for the predicted class
        shap.summary_plot(shap_values_full[pred_class_idx], X_train, show=False)
        plt.title(f"SHAP Contributions for {prediction} Congestion Risk", fontsize=11, pad=15)
        plt.tight_layout()
        plot_path = os.path.join(STATIC_IMG_DIR, "shap_summary_traffic.png")
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"[XAI Traffic Plot Error] {e}")

    # Generate Feature Importance JSON
    importances = model.feature_importances_
    feat_importance = [
        {"feature": feature_labels.get(feat, feat), "importance": float(imp)}
        for feat, imp in zip(features, importances)
    ]
    # Sort by importance descending
    feat_importance = sorted(feat_importance, key=lambda x: x["importance"], reverse=True)

    return {
        "prediction": prediction,
        "probabilities": {classes[i]: float(prob[i]) for i in range(3)},
        "contributions": contributions,
        "feature_importance": feat_importance,
        "plot_url": "/static/images/shap_summary_traffic.png"
    }

# ==========================================
# 2. POLLUTION ML MODEL
# ==========================================
def train_pollution_model():
    """
    Fetches pollution data from Supabase, fits a RandomForestRegressor (target = AQI),
    and returns (model, feature_names, X_train_dataframe).
    """
    db_records = supabase_client.get_all_pollution_data()
    
    if len(db_records) < 15:
        print("[XAI Pollution] Insufficient database records. Generating synthetic training data...")
        np.random.seed(101)
        n_samples = 150
        
        pm25 = np.random.uniform(5.0, 150.0, n_samples)
        pm10 = pm25 * 1.4 + np.random.normal(0, 10, n_samples)
        pm10 = np.clip(pm10, 8.0, 250.0)
        co2 = 300.0 + (pm25 * 2.2) + np.random.uniform(50, 150, n_samples)
        noise_level = 40.0 + (pm25 * 0.25) + np.random.normal(0, 5, n_samples)
        noise_level = np.clip(noise_level, 35.0, 95.0)
        
        # Calculate AQI based on EPA standard representation
        aqi = (pm25 * 1.2) + (pm10 * 0.3) + ((co2 - 350) * 0.1) + np.random.normal(0, 5, n_samples)
        aqi = np.clip(aqi, 10.0, 300.0).astype(int)
        
        df = pd.DataFrame({
            'pm25': pm25,
            'pm10': pm10,
            'co2': co2,
            'noise_level': noise_level,
            'target': aqi
        })
    else:
        data_list = []
        for r in db_records:
            data_list.append({
                'pm25': float(r.get('pm25')),
                'pm10': float(r.get('pm10')),
                'co2': float(r.get('co2')),
                'noise_level': float(r.get('noise_level')),
                'target': int(r.get('aqi'))
            })
        df = pd.DataFrame(data_list)
        
    feature_cols = ['pm25', 'pm10', 'co2', 'noise_level']
    X = df[feature_cols]
    y = df['target']
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    return model, feature_cols, X

def get_pollution_explanation(pm25, pm10, co2, noise_level):
    """
    Predicts AQI and generates SHAP values explaining what variables caused it.
    """
    model, features, X_train = train_pollution_model()
    
    input_data = pd.DataFrame([[pm25, pm10, co2, noise_level]], columns=features)
    
    # Predict continuous AQI
    predicted_aqi = float(model.predict(input_data)[0])
    
    # Classify Risk level based on predicted AQI
    if predicted_aqi <= 50:
        risk_level = "Low (Good)"
    elif predicted_aqi <= 100:
        risk_level = "Moderate"
    elif predicted_aqi <= 150:
        risk_level = "Unhealthy for Sensitive Groups"
    else:
        risk_level = "High (Unhealthy)"
        
    # SHAP Explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(input_data)[0]
    base_value = float(explainer.expected_value)
    
    contributions = []
    feature_labels = {
        'pm25': 'PM2.5 Concentration',
        'pm10': 'PM10 Concentration',
        'co2': 'Carbon Dioxide (CO2)',
        'noise_level': 'Noise Level (dB)'
    }
    
    for feat, val in zip(features, shap_values):
        contributions.append({
            "feature": feat,
            "display_name": feature_labels.get(feat, feat),
            "value": float(input_data[feat].iloc[0]),
            "shap_value": float(val),
            "effect": "Increases Pollution" if val > 0 else "Reduces Pollution"
        })
        
    # Generate SHAP Summary Plot image
    try:
        plt.figure(figsize=(6, 4))
        shap_values_full = explainer.shap_values(X_train)
        shap.summary_plot(shap_values_full, X_train, show=False)
        plt.title("SHAP Contributions for AQI Predictions", fontsize=11, pad=15)
        plt.tight_layout()
        plot_path = os.path.join(STATIC_IMG_DIR, "shap_summary_pollution.png")
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"[XAI Pollution Plot Error] {e}")

    # Generate Feature Importance
    importances = model.feature_importances_
    feat_importance = [
        {"feature": feature_labels.get(feat, feat), "importance": float(imp)}
        for feat, imp in zip(features, importances)
    ]
    feat_importance = sorted(feat_importance, key=lambda x: x["importance"], reverse=True)

    return {
        "predicted_aqi": round(predicted_aqi, 1),
        "risk_level": risk_level,
        "base_value": base_value,
        "contributions": contributions,
        "feature_importance": feat_importance,
        "plot_url": "/static/images/shap_summary_pollution.png"
    }
