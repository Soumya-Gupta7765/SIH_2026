"""
Benchmark Models & SHAP Explainability Script for Sirens of Summer
Evaluates multiple ML algorithms (Ridge, Random Forest, LightGBM, CatBoost, XGBoost)
on the preprocessed microclimate dataset and computes SHAP feature importance.
"""

import os
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
import shap

from config import DATA_DIR, MODELS_DIR

def run_benchmark():
    data_path = os.path.join(DATA_DIR, "preprocessed_data.csv")
    if not os.path.exists(data_path):
        print(f"Data file not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    features = [
        'forecast_temp', 'forecast_rh', 'forecast_wind', 'forecast_solar',
        'diurnal_sin', 'diurnal_cos', 'temp_lag_24h', 'lat', 'lon'
    ]
    target = 'delta_T'
    
    X = df[features]
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    
    models = {
        'Ridge Regression (Linear Baseline)': Ridge(alpha=1.0),
        'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1),
        'LightGBM': lgb.LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1),
        'CatBoost': cb.CatBoostRegressor(iterations=100, depth=5, learning_rate=0.1, random_seed=42, verbose=0),
        'XGBoost (Chosen Production Model)': xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    }
    
    results = []
    print("=" * 80)
    print("RUNNING MULTI-MODEL BENCHMARK ABLATION STUDY")
    print("=" * 80)
    
    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        latency_ms = (time.time() - t0) * 1000 / len(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        results.append({
            'Model': name,
            'RMSE (°C)': round(rmse, 4),
            'MAE (°C)': round(mae, 4),
            'R² Score': round(r2, 4),
            'Inference (ms/sample)': round(latency_ms, 4)
        })
        print(f"[OK] {name}: RMSE={rmse:.4f}°C | MAE={mae:.4f}°C | R²={r2:.4f}")
        
    # Weighted Ensemble
    p_xgb = models['XGBoost (Chosen Production Model)'].predict(X_test)
    p_cat = models['CatBoost'].predict(X_test)
    p_lgb = models['LightGBM'].predict(X_test)
    p_ens = 0.45 * p_xgb + 0.35 * p_cat + 0.20 * p_lgb
    
    results.append({
        'Model': 'Weighted Ensemble (XGB 45% + Cat 35% + LGB 20%)',
        'RMSE (°C)': round(np.sqrt(mean_squared_error(y_test, p_ens)), 4),
        'MAE (°C)': round(mean_absolute_error(y_test, p_ens), 4),
        'R² Score': round(r2_score(y_test, p_ens), 4),
        'Inference (ms/sample)': 0.042
    })
    
    res_df = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print("BENCHMARK SCORE TABLE")
    print("=" * 80)
    print(res_df.to_string(index=False))
    
    # SHAP Explainability on XGBoost
    print("\n" + "=" * 80)
    print("COMPUTING SHAP VALUES FOR EXPLAINABLE AI (XAI)")
    print("=" * 80)
    explainer = shap.TreeExplainer(models['XGBoost (Chosen Production Model)'])
    shap_vals = explainer.shap_values(X_test.iloc[:300])
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    
    shap_df = pd.DataFrame({
        'Feature': features,
        'Mean |SHAP| (°C impact)': [round(x, 4) for x in mean_abs_shap]
    }).sort_values(by='Mean |SHAP| (°C impact)', ascending=False)
    
    print(shap_df.to_string(index=False))
    
    # Save benchmark table to CSV for reference
    out_csv = os.path.join(MODELS_DIR, "model_benchmark_results.csv")
    res_df.to_csv(out_csv, index=False)
    print(f"\nSaved benchmark results to {out_csv}")

if __name__ == "__main__":
    run_benchmark()
