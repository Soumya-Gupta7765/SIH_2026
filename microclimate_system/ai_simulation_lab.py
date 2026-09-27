"""
AI Simulation Lab & What-If Policy Sandbox Engine
Sirens of Summer - Microclimate Heat Alert System

Allows urban planners, disaster response teams, and researchers to:
1. Adjust climate forcing parameters (Ambient heat rise, humidity surges, wind stagnation)
2. Simulate urban policy interventions (Afforestation/NDVI, Cool Roof coatings, Misting, Slum insulation)
3. Evaluate physiological UTCI shifts, geriatric risk reductions, and power grid cooling relief in real-time.
"""

import numpy as np
import pandas as pd
from scripts.generate_ward_data import calculate_utci_approx, get_risk_tier, get_elderly_risk_tier

PRESET_SCENARIOS = {
    "⚡ El Niño Super Heatwave (+4.0°C Regional Anomaly)": {
        "description": "Simulates severe macro-synoptic heat dome with stagnant winds and moderate humidity.",
        "ambient_delta_c": 4.0,
        "rh_delta_pct": 5.0,
        "wind_delta_mps": -1.2,
        "solar_delta_wm2": 120.0,
        "afforestation_pct": 0.0,
        "cool_roof_pct": 0.0,
        "misting_units": 0.0,
        "slum_insulation_pct": 0.0
    },
    "🌳 NDMA 'Cool Delhi 2030' Mission (Greenery & Cool Roofs)": {
        "description": "Massive civic intervention: 35% cool roofs on tin/concrete, 25% tree canopy afforestation.",
        "ambient_delta_c": 0.0,
        "rh_delta_pct": 0.0,
        "wind_delta_mps": 0.0,
        "solar_delta_wm2": 0.0,
        "afforestation_pct": 25.0,
        "cool_roof_pct": 35.0,
        "misting_units": 1.5,
        "slum_insulation_pct": 20.0
    },
    "💧 Wet-Bulb Humidity Crisis (+2.5°C & +25% Humidity)": {
        "description": "Simulates monsoon-break pre-rain sultry conditions where humidity severely impairs sweat evaporation.",
        "ambient_delta_c": 2.5,
        "rh_delta_pct": 25.0,
        "wind_delta_mps": -0.8,
        "solar_delta_wm2": -50.0,
        "afforestation_pct": 0.0,
        "cool_roof_pct": 0.0,
        "misting_units": 0.0,
        "slum_insulation_pct": 0.0
    },
    "🏠 Targeted Informal Settlement Slum Retrofit": {
        "description": "Targeted deployment of white reflective coatings, insulation nets, and misting in dense slum clusters.",
        "ambient_delta_c": 0.0,
        "rh_delta_pct": 0.0,
        "wind_delta_mps": 0.0,
        "solar_delta_wm2": 0.0,
        "afforestation_pct": 10.0,
        "cool_roof_pct": 60.0,
        "misting_units": 3.5,
        "slum_insulation_pct": 50.0
    }
}

def run_climate_simulation(
    df_baseline: pd.DataFrame,
    ambient_delta_c: float = 0.0,
    rh_delta_pct: float = 0.0,
    wind_delta_mps: float = 0.0,
    solar_delta_wm2: float = 0.0,
    afforestation_pct: float = 0.0,
    cool_roof_pct: float = 0.0,
    misting_units: float = 0.0,
    slum_insulation_pct: float = 0.0
):
    """
    Vectorized computation of simulated microclimates across all wards.
    """
    if df_baseline.empty:
        return {}

    sim = df_baseline.copy()
    
    # 1. Effective physical proxies under policy interventions
    eff_ndvi = np.clip(sim['ndvi_vegetation'] * (1.0 + afforestation_pct / 100.0), 0.04, 0.65)
    eff_built = np.clip(sim['built_up_ratio'] * (1.0 - (cool_roof_pct / 100.0) * 0.35), 0.20, 0.95)
    eff_slum = np.clip(sim['slum_density_pct'] * (1.0 - (slum_insulation_pct / 100.0) * 0.55), 0.5, 35.0)
    
    # Misting cooling effect (evaporative localized sensible cooling)
    misting_cooling = misting_units * 0.42 # up to ~2.1°C
    
    # 2. Simulated Delta T (UHI microclimate bias)
    sim['sim_delta_T'] = (2.6 * (eff_built - 0.5)) - (3.8 * (eff_ndvi - 0.2)) + (0.05 * (eff_slum - 10.0)) - misting_cooling
    sim['sim_delta_T'] = sim['sim_delta_T'].round(2)
    
    # 3. Simulated Atmospheric Weather
    sim['sim_forecast_temp'] = (sim['forecast_temp'] + ambient_delta_c).round(1)
    sim['sim_predicted_temp'] = (sim['sim_forecast_temp'] + sim['sim_delta_T']).round(1)
    sim['sim_rh'] = np.clip(sim['forecast_rh'] + rh_delta_pct, 10.0, 95.0).round(1)
    sim['sim_wind'] = np.clip(sim['forecast_wind'] + wind_delta_mps, 0.5, 25.0).round(1)
    sim['sim_solar'] = np.clip(sim['forecast_solar'] + solar_delta_wm2, 80.0, 1150.0).round(1)
    
    # 4. Simulated UTCI (Vectorized approximation)
    mrt = sim['sim_predicted_temp'] + (sim['sim_solar'] * 0.012)
    vapor_press = (sim['sim_rh'] / 100.0) * 6.105 * np.exp((17.27 * sim['sim_predicted_temp']) / (237.7 + sim['sim_predicted_temp']))
    sim['sim_utci'] = sim['sim_predicted_temp'] + 0.25 * (mrt - sim['sim_predicted_temp']) + 0.18 * vapor_press - 0.7 * np.sqrt(sim['sim_wind'])
    sim['sim_utci'] = sim['sim_utci'].round(1)
    
    # 5. Risk tier categorizations
    def categorize_risk(u):
        if u >= 43.0:
            return "Extreme Danger", "#8b0000"
        elif u >= 38.0:
            return "Critical Heat", "#e53935"
        elif u >= 32.0:
            return "Moderate Risk", "#fb8c00"
        else:
            return "Safe", "#2e7d32"
            
    def categorize_elderly(u):
        if u >= 42.0:
            return "Severe Geriatric Danger", "#8b0000"
        elif u >= 37.0:
            return "Critical Geriatric Strain", "#e53935"
        elif u >= 32.0:
            return "Moderate Geriatric Risk", "#fb8c00"
        else:
            return "Normal Monitoring", "#2e7d32"

    risk_results = [categorize_risk(u) for u in sim['sim_utci']]
    sim['sim_risk_level'] = [r[0] for r in risk_results]
    sim['sim_risk_color'] = [r[1] for r in risk_results]
    
    eld_results = [categorize_elderly(u) for u in sim['sim_utci']]
    sim['sim_elderly_risk'] = [e[0] for e in eld_results]
    sim['sim_elderly_color'] = [e[1] for e in eld_results]
    
    # 6. Differences & Metric Aggregations
    sim['utci_diff'] = (sim['sim_utci'] - sim['utci']).round(1)
    sim['temp_diff'] = (sim['sim_predicted_temp'] - sim['predicted_temp']).round(1)
    
    baseline_extreme = len(sim[sim['risk_level'] == 'Extreme Danger'])
    sim_extreme = len(sim[sim['sim_risk_level'] == 'Extreme Danger'])
    
    baseline_critical = len(sim[sim['risk_level'] == 'Critical Heat'])
    sim_critical = len(sim[sim['sim_risk_level'] == 'Critical Heat'])
    
    baseline_avg_utci = sim['utci'].mean()
    sim_avg_utci = sim['sim_utci'].mean()
    avg_utci_diff = round(sim_avg_utci - baseline_avg_utci, 2)
    
    # Elderly metrics
    baseline_eld_severe = sim[sim['elderly_risk'] == 'Severe Geriatric Danger']['elderly_population'].sum() if 'elderly_population' in sim.columns else 0
    sim_eld_severe = sim[sim['sim_elderly_risk'] == 'Severe Geriatric Danger']['elderly_population'].sum() if 'elderly_population' in sim.columns else 0
    elderly_protected_delta = int(baseline_eld_severe - sim_eld_severe)
    
    # Power grid cooling load proxy: ~22 MW per 1°C regional thermal shift in Delhi
    power_grid_mw_delta = round(-avg_utci_diff * 22.0, 1)
    
    return {
        "sim_df": sim,
        "baseline_extreme_count": baseline_extreme,
        "sim_extreme_count": sim_extreme,
        "extreme_delta": sim_extreme - baseline_extreme,
        "baseline_critical_count": baseline_critical,
        "sim_critical_count": sim_critical,
        "baseline_avg_utci": round(baseline_avg_utci, 1),
        "sim_avg_utci": round(sim_avg_utci, 1),
        "avg_utci_diff": avg_utci_diff,
        "baseline_eld_severe": int(baseline_eld_severe),
        "sim_eld_severe": int(sim_eld_severe),
        "elderly_protected_delta": elderly_protected_delta,
        "power_grid_mw_delta": power_grid_mw_delta
    }
