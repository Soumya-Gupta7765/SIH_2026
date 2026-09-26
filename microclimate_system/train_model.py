import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from config import DATA_DIR, MODELS_DIR

def train():
    print("Loading preprocessed data...")
    data_path = os.path.join(DATA_DIR, "preprocessed_data.csv")
    df = pd.read_csv(data_path)
    
    # Features (X) and Target (y)
    features = [
        'forecast_temp', 
        'forecast_rh', 
        'forecast_wind', 
        'forecast_solar',
        'diurnal_sin', 
        'diurnal_cos', 
        'temp_lag_24h',
        'lat',
        'lon'
    ]
    target = 'delta_T'
    
    X = df[features]
    y = df[target]
    
    print("Splitting data into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    print("Training XGBoost Regressor...")
    model = xgb.XGBRegressor(
        n_estimators=100, 
        max_depth=5, 
        learning_rate=0.1, 
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    print("Evaluating model...")
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    print(f"Test MSE: {mse:.4f}")
    print(f"Test MAE: {mae:.4f}")
    
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, predictions, alpha=0.5)
    
    # Plot perfect prediction line
    min_val = min(y_test.min(), predictions.min())
    max_val = max(y_test.max(), predictions.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
    
    plt.xlabel('Actual Delta T (°C)')
    plt.ylabel('Predicted Delta T (°C)')
    plt.title('XGBoost Predictions vs Actual on Test Set')
    plt.tight_layout()
    plot_path = os.path.join(MODELS_DIR, 'test_accuracy.png')
    plt.savefig(plot_path)
    print(f"Saved accuracy plot to {plot_path}")
    
    # Feature Importance
    importances = model.feature_importances_
    for i, col in enumerate(features):
        print(f"Feature '{col}' importance: {importances[i]:.4f}")
        
    model_path = os.path.join(MODELS_DIR, "xgboost_model.json")
    model.save_model(model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train()
