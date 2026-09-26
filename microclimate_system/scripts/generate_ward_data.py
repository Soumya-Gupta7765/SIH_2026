"""
Generate Enriched Ward-Level Geospatial Dataset with 5-Day Horizon & Worst-Case Peaks
Combines:
- 272 Delhi MCD Wards (GeoJSON boundaries)
- DUSIB Slum Clusters & Housing Material Distribution
- Demographic Population Density (Census / WorldPop)
- Satellite NDVI (Vegetation) and Built-up Ratios
- Open-Meteo 120-Hour Synoptic Forecast & Microclimate Downscaling Physics (Delta T & UTCI)
Output:
- data/delhi_wards_enriched.geojson (contains day-by-day 1-5 + worst-case peak properties)
- data/delhi_wards_summary.csv (contains full 5-day horizon summary per ward)
"""

import os
import json
import numpy as np
import pandas as pd
from shapely.geometry import shape

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
SPATIAL_RAW_DIR = os.path.join(DATA_DIR, "spatial_raw")

def calculate_utci_approx(temp_c, rh_pct, wind_mps, solar_wm2):
    """
    Computes Universal Thermal Climate Index (UTCI) approximation.
    Incorporates temperature, relative humidity, wind speed, and mean radiant temp proxy.
    """
    mrt = temp_c + (solar_wm2 * 0.012)
    vapor_press = (rh_pct / 100.0) * 6.105 * np.exp((17.27 * temp_c) / (237.7 + temp_c))
    utci = temp_c + 0.25 * (mrt - temp_c) + 0.18 * vapor_press - 0.7 * np.sqrt(max(wind_mps, 0.5))
    return round(float(utci), 1)

def get_risk_tier(utci):
    if utci >= 43.0:
        return "Extreme Danger", "#8b0000", "🚨 EMERGENCY: Open 24/7 cooling centers, halt outdoor labor (11am-4pm), dispatch emergency water tankers to slum clusters, activate hospital heat-stroke protocols."
    elif utci >= 38.0:
        return "Critical Heat", "#e53935", "🔥 CRITICAL: Activate municipal misting fans, set up ORS hydration booths, advise elderly/children to remain indoors, halt non-essential outdoor work."
    elif utci >= 32.0:
        return "Moderate Risk", "#fb8c00", "⚠️ ADVISORY: Enforce hydration breaks for outdoor workers, distribute ORS at transit hubs, maintain continuous water supplies in high-density settlements."
    else:
        return "Safe", "#2e7d32", "✅ NORMAL: Routine conditions, maintain standard municipal water surveillance, no emergency restrictions."

def generate_enriched_wards():
    print("Generating Enriched 5-Day Ward-Level Dataset...")
    
    # 1. Load 272 MCD Wards
    wards_path = os.path.join(SPATIAL_RAW_DIR, "delhi_mcd_wards.geojson")
    with open(wards_path, "r", encoding="utf-8") as f:
        wards_geo = json.load(f)
        
    # 2. Load Zone Polygons for spatial matching
    ncr_path = os.path.join(DATA_DIR, "ncr_zones.geojson")
    with open(ncr_path, "r", encoding="utf-8") as f:
        ncr_geo = json.load(f)
    zone_polys = {f["properties"]["zone_name"]: shape(f["geometry"]) for f in ncr_geo["features"]}
    
    # 3. Load Spatial Features (NDVI, Slum, Pop Density)
    spatial_features_path = os.path.join(SPATIAL_RAW_DIR, "delhi_ncr_spatial_features.csv")
    df_spatial = pd.read_csv(spatial_features_path).set_index("zone_name")
    
    # 4. Load Inference Weather Data (Hourly 120-hour forecast)
    inference_path = os.path.join(DATA_DIR, "inference_results.csv")
    df_inf = pd.read_csv(inference_path)
    df_inf['date'] = pd.to_datetime(df_inf['date'])
    
    forecast_days = sorted(df_inf['date'].dt.date.unique())[:5]
    print(f"Extracted 5 forecast days: {forecast_days}")
    
    # Precompute zone daily peaks for Day 1 to Day 5, plus overall 5-day worst-case
    zone_day_peaks = {}
    zone_worst_peaks = {}
    
    for zone in df_inf['zone_name'].unique():
        z_df = df_inf[df_inf['zone_name'] == zone]
        zone_day_peaks[zone] = {}
        
        for d_idx, day_date in enumerate(forecast_days, start=1):
            d_df = z_df[z_df['date'].dt.date == day_date]
            if not d_df.empty:
                zone_day_peaks[zone][d_idx] = {
                    "forecast_temp": round(float(d_df['forecast_temp'].max()), 1),
                    "forecast_rh": round(float(d_df['forecast_rh'].mean()), 1),
                    "forecast_wind": round(float(d_df['forecast_wind'].mean()), 1),
                    "forecast_solar": round(float(d_df['forecast_solar'].max()), 1),
                }
            else:
                zone_day_peaks[zone][d_idx] = {
                    "forecast_temp": 32.0, "forecast_rh": 50.0, "forecast_wind": 3.0, "forecast_solar": 700.0
                }
                
        # Overall 5-day worst peak
        zone_worst_peaks[zone] = {
            "forecast_temp": round(float(z_df['forecast_temp'].max()), 1),
            "forecast_rh": round(float(z_df['forecast_rh'].mean()), 1),
            "forecast_wind": round(float(z_df['forecast_wind'].mean()), 1),
            "forecast_solar": round(float(z_df['forecast_solar'].max()), 1),
        }
        
    enriched_features = []
    summary_rows = []
    corp_map = {"E": "East Delhi MCD", "N": "North Delhi MCD", "S": "South Delhi MCD"}
    
    for i, feature in enumerate(wards_geo["features"]):
        poly = shape(feature["geometry"])
        centroid = poly.centroid
        area_sqkm = round(poly.area * 111.32 * 111.32 * np.cos(np.radians(centroid.y)), 2)
        
        props = feature.get("properties", {})
        zone_code = props.get("zone", "N")
        ward_num = props.get("id", i + 1)
        unique_id = props.get("unique", f"{ward_num:03d}{zone_code}")
        corporation = corp_map.get(zone_code, "Delhi Municipal Corporation")
        
        # Spatial match to zone
        matched_zone = None
        for zname, zpoly in zone_polys.items():
            if zpoly.contains(centroid):
                matched_zone = zname
                break
        if not matched_zone:
            matched_zone = min(zone_polys.keys(), key=lambda z: zone_polys[z].distance(centroid))
            
        # Get baseline features
        if matched_zone in df_spatial.index:
            z_feat = df_spatial.loc[matched_zone]
            base_pop_density = int(z_feat["pop_density_per_km2"])
            base_ndvi = float(z_feat["ndvi_vegetation"])
            base_built = float(z_feat["built_up_ratio"])
            base_slum = float(z_feat["slum_density_pct"])
        else:
            base_pop_density = 15000
            base_ndvi = 0.20
            base_built = 0.70
            base_slum = 12.0
            
        # Deterministic micro-variations
        np.random.seed(int(ward_num) * 37 + ord(zone_code[0]))
        ward_ndvi = round(float(np.clip(base_ndvi + np.random.uniform(-0.04, 0.04), 0.05, 0.48)), 3)
        ward_built = round(float(np.clip(base_built + np.random.uniform(-0.05, 0.05), 0.35, 0.92)), 2)
        ward_slum = round(float(np.clip(base_slum + np.random.uniform(-3.5, 3.5), 1.0, 35.0)), 1)
        ward_pop_density = int(np.clip(base_pop_density + np.random.randint(-2500, 3000), 2000, 48000))
        
        # Microclimate Downscaling Physics Bias
        delta_T = round((2.6 * (ward_built - 0.5)) - (3.8 * (ward_ndvi - 0.2)) + (0.05 * (ward_slum - 10.0)), 2)
        ward_display_name = f"Ward {unique_id} ({matched_zone})"
        
        ward_dict = {
            "ward_id": unique_id,
            "ward_name": ward_display_name,
            "corporation": corporation,
            "zone_name": matched_zone,
            "lat": round(centroid.y, 4),
            "lon": round(centroid.x, 4),
            "area_sqkm": area_sqkm,
            "delta_T": delta_T,
            "ndvi_vegetation": ward_ndvi,
            "built_up_ratio": ward_built,
            "slum_density_pct": ward_slum,
            "pop_density_per_km2": ward_pop_density
        }
        
        # Calculate Day 1 through Day 5 values
        for d_idx in range(1, 6):
            d_weather = zone_day_peaks.get(matched_zone, {}).get(d_idx, {
                "forecast_temp": 32.0, "forecast_rh": 50.0, "forecast_wind": 3.0, "forecast_solar": 700.0
            })
            d_base_temp = d_weather["forecast_temp"]
            d_pred_temp = round(d_base_temp + delta_T, 1)
            d_utci = calculate_utci_approx(d_pred_temp, d_weather["forecast_rh"], d_weather["forecast_wind"], d_weather["forecast_solar"])
            d_risk, d_color, d_measures = get_risk_tier(d_utci)
            d_action = d_measures.split(":")[1].split(",")[0].strip() if ":" in d_measures else d_measures
            
            ward_dict[f"d{d_idx}_base_temp"] = d_base_temp
            ward_dict[f"d{d_idx}_temp"] = d_pred_temp
            ward_dict[f"d{d_idx}_rh"] = d_weather["forecast_rh"]
            ward_dict[f"d{d_idx}_wind"] = d_weather["forecast_wind"]
            ward_dict[f"d{d_idx}_solar"] = d_weather["forecast_solar"]
            ward_dict[f"d{d_idx}_utci"] = d_utci
            ward_dict[f"d{d_idx}_risk"] = d_risk
            ward_dict[f"d{d_idx}_color"] = d_color
            ward_dict[f"d{d_idx}_temp_display"] = f"{d_pred_temp} °C (ΔT: {delta_T:+.1f} °C)"
            ward_dict[f"d{d_idx}_utci_display"] = f"{d_utci} °C ({d_risk})"
            ward_dict[f"d{d_idx}_action"] = d_action
            ward_dict[f"d{d_idx}_measures"] = d_measures
            
        # Overall 5-Day Worst Case
        w_weather = zone_worst_peaks.get(matched_zone, {
            "forecast_temp": 34.5, "forecast_rh": 48.0, "forecast_wind": 3.2, "forecast_solar": 750.0
        })
        w_base_temp = w_weather["forecast_temp"]
        w_pred_temp = round(w_base_temp + delta_T, 1)
        w_utci = calculate_utci_approx(w_pred_temp, w_weather["forecast_rh"], w_weather["forecast_wind"], w_weather["forecast_solar"])
        w_risk, w_color, w_measures = get_risk_tier(w_utci)
        w_action = w_measures.split(":")[1].split(",")[0].strip() if ":" in w_measures else w_measures
        
        ward_dict["worst_base_temp"] = w_base_temp
        ward_dict["worst_temp"] = w_pred_temp
        ward_dict["worst_rh"] = w_weather["forecast_rh"]
        ward_dict["worst_wind"] = w_weather["forecast_wind"]
        ward_dict["worst_solar"] = w_weather["forecast_solar"]
        ward_dict["worst_utci"] = w_utci
        ward_dict["worst_risk"] = w_risk
        ward_dict["worst_color"] = w_color
        ward_dict["worst_temp_display"] = f"{w_pred_temp} °C (ΔT: {delta_T:+.1f} °C)"
        ward_dict["worst_utci_display"] = f"{w_utci} °C ({w_risk})"
        ward_dict["worst_action"] = w_action
        ward_dict["worst_measures"] = w_measures
        
        # Default active values (starts as worst-case peak)
        ward_dict["forecast_temp"] = w_base_temp
        ward_dict["predicted_temp"] = w_pred_temp
        ward_dict["forecast_rh"] = w_weather["forecast_rh"]
        ward_dict["forecast_wind"] = w_weather["forecast_wind"]
        ward_dict["forecast_solar"] = w_weather["forecast_solar"]
        ward_dict["utci"] = w_utci
        ward_dict["risk_level"] = w_risk
        ward_dict["risk_color"] = w_color
        ward_dict["temp_display"] = ward_dict["worst_temp_display"]
        ward_dict["utci_display"] = ward_dict["worst_utci_display"]
        ward_dict["action_summary"] = w_action
        ward_dict["measures"] = w_measures
        
        enriched_features.append({
            "type": "Feature",
            "geometry": feature["geometry"],
            "properties": ward_dict
        })
        summary_rows.append(ward_dict)
        
    # Write enriched GeoJSON
    out_geojson_path = os.path.join(DATA_DIR, "delhi_wards_enriched.geojson")
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": enriched_features}, f)
    print(f"Saved {len(enriched_features)} enriched 5-day ward polygons to {out_geojson_path}")
    
    # Write summary CSV
    df_summary = pd.DataFrame(summary_rows)
    out_csv_path = os.path.join(DATA_DIR, "delhi_wards_summary.csv")
    df_summary.to_csv(out_csv_path, index=False)
    print(f"Saved 5-day ward summary table to {out_csv_path}")
    return True

if __name__ == "__main__":
    generate_enriched_wards()
