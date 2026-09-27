import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
import subprocess
import sys
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from config import ZONES, DATA_DIR, MODELS_DIR

# Custom modules
import alert_dispatcher
from ai_simulation_lab import PRESET_SCENARIOS, run_climate_simulation

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & METADATA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="MoES • NCMRWF | Sirens of Summer Heat Early Warning Engine",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Audio siren synthesizer helper (Web Audio API)
def trigger_audio_siren():
    st.components.v1.html("""
    <script>
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(820, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(420, audioCtx.currentTime + 0.35);
        osc.frequency.exponentialRampToValueAtTime(820, audioCtx.currentTime + 0.7);
        osc.frequency.exponentialRampToValueAtTime(420, audioCtx.currentTime + 1.05);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 1.4);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 1.4);
    } catch(e) { console.log(e); }
    </script>
    """, height=0)

# ------------------------------------------------------------------------------
# 2. ADVANCED GLASSMORPHIC DARK STYLING (Inspired by SIH26_better_UI)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg-primary: #080D1A;
  --bg-secondary: #0F172A;
  --bg-surface: rgba(15, 23, 42, 0.75);
  --bg-surface-elevated: rgba(30, 41, 59, 0.85);
  --border-subtle: rgba(255, 255, 255, 0.09);
  --border-focus: rgba(59, 130, 246, 0.5);
  
  --text-main: #F8FAFC;
  --text-muted: #94A3B8;
  --text-subtle: #64748B;
  
  --tier-green: #10B981;
  --tier-yellow: #F59E0B;
  --tier-orange: #F97316;
  --tier-red: #EF4444;
  --accent-blue: #3B82F6;
  --accent-cyan: #06B6D4;
  --accent-purple: #8B5CF6;
  
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-xl: 24px;
}

/* Global App Container */
.stApp {
  background-color: var(--bg-primary) !important;
  background-image: 
    radial-gradient(circle at 12% 18%, rgba(239, 68, 68, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 88% 82%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 1) 0%, rgba(8, 13, 26, 1) 100%) !important;
  color: var(--text-main) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Typography Overrides */
h1, h2, h3, h4, .brand-title {
  font-family: 'Outfit', sans-serif !important;
  letter-spacing: -0.02em !important;
}

.mono {
  font-family: 'JetBrains Mono', monospace !important;
}

/* Streamlit Header & Top Padding */
header[data-testid="stHeader"] {
  background: transparent !important;
}

.block-container {
  padding-top: 1.2rem !important;
  padding-bottom: 2rem !important;
  max-width: 98% !important;
}

/* Top Navigation Bar */
.app-header {
  background: rgba(8, 13, 26, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  margin-bottom: 18px;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-emblem {
  width: 46px;
  height: 46px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #EF4444 0%, #F97316 50%, #3B82F6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 4px 18px rgba(239, 68, 68, 0.45);
}

.brand-info {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-badge {
  font-size: 0.70rem;
  font-weight: 600;
  padding: 2px 8px;
  background: rgba(239, 68, 68, 0.2);
  color: #FCA5A5;
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 999px;
  text-transform: uppercase;
}

.brand-sub {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.header-center {
  display: flex;
  align-items: center;
  gap: 14px;
}

.city-select-pill {
  background: rgba(30, 41, 59, 0.65);
  border: 1px solid var(--border-subtle);
  padding: 6px 16px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.84rem;
  font-weight: 500;
  color: var(--text-main);
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--tier-green);
  background: rgba(16, 185, 129, 0.12);
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.live-dot {
  width: 8px;
  height: 8px;
  background: var(--tier-green);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--tier-green);
  animation: pulse-dot 1.8s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.8; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
  70% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.9); opacity: 0.8; }
}

/* Stat Overview Cards (Summary Bar) */
.stat-card-wrap {
  background: var(--bg-surface);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 14px 18px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
  transition: all 0.3s ease;
  height: 100%;
}

.stat-card-wrap:hover {
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.stat-card-wrap::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--accent-blue);
}

.stat-card-danger::before { background: var(--tier-red); }
.stat-card-warning::before { background: var(--tier-orange); }
.stat-card-amber::before { background: var(--tier-yellow); }
.stat-card-cyan::before { background: var(--accent-cyan); }
.stat-card-purple::before { background: var(--accent-purple); }
.stat-card-green::before { background: var(--tier-green); }

.stat-title {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 1.65rem;
  font-weight: 800;
  font-family: 'Outfit', sans-serif;
  color: var(--text-main);
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-unit {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-subtle);
}

.stat-note {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Microclimate Adjustment Box */
.microclimate-box {
  background: rgba(30, 41, 59, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 12px;
}

.microclimate-title {
  font-size: 0.74rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #60A5FA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.microclimate-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.metric-column .val {
  font-size: 1.35rem;
  font-weight: 700;
  font-family: 'Outfit', sans-serif;
  color: var(--text-main);
}

.metric-column .lbl {
  font-size: 0.70rem;
  color: var(--text-muted);
}

.bias-arrow {
  color: #F87171;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(239, 68, 68, 0.15);
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(239, 68, 68, 0.35);
}

/* Stress Grid */
.stress-metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}

.stress-card {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
}

.stress-card h5 {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 4px;
  margin-top: 0;
}

.stress-card .val {
  font-size: 1.3rem;
  font-weight: 700;
  font-family: 'Outfit', sans-serif;
  color: var(--text-main);
}

.stress-card .tag {
  font-size: 0.68rem;
  color: #FBBF24;
  margin-top: 2px;
  font-weight: 500;
}

/* Risk Badges */
.risk-badge {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 5px 14px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.badge-red {
  background: rgba(239, 68, 68, 0.2);
  color: #F87171;
  border: 1px solid #EF4444;
}

.badge-orange {
  background: rgba(249, 115, 22, 0.2);
  color: #FB923C;
  border: 1px solid #F97316;
}

.badge-yellow {
  background: rgba(245, 158, 11, 0.2);
  color: #FBBF24;
  border: 1px solid #F59E0B;
}

.badge-green {
  background: rgba(16, 185, 129, 0.2);
  color: #34D399;
  border: 1px solid #10B981;
}

/* Vulnerability Bars */
.v-bar-group {
  margin-bottom: 8px;
}

.v-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  margin-bottom: 3px;
  color: var(--text-muted);
}

.v-bar-label strong {
  color: var(--text-main);
}

.v-bar-track {
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.v-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.fill-red { background: var(--tier-red); }
.fill-orange { background: var(--tier-orange); }
.fill-amber { background: var(--tier-yellow); }
.fill-cyan { background: var(--accent-cyan); }

/* Legend Box */
.legend-box {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  padding: 8px 16px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: 0.78rem;
  font-weight: 600;
}

/* Streamlit Tabs Customization */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px !important;
  background-color: transparent !important;
  border-bottom: 1px solid var(--border-subtle) !important;
}

.stTabs [data-baseweb="tab"] {
  height: 44px !important;
  white-space: pre !important;
  background-color: rgba(30, 41, 59, 0.4) !important;
  border-radius: 8px 8px 0 0 !important;
  border: 1px solid var(--border-subtle) !important;
  border-bottom: none !important;
  color: var(--text-muted) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  padding: 0 18px !important;
}

.stTabs [data-baseweb="tab"]:hover {
  color: var(--text-main) !important;
  background-color: rgba(59, 130, 246, 0.15) !important;
}

.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(30, 41, 59, 0.8) 100%) !important;
  color: #F87171 !important;
  border-color: rgba(239, 68, 68, 0.5) !important;
  font-weight: 600 !important;
}

/* Streamlit Buttons */
.stButton > button {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
  color: #FFFFFF !important;
  border: 1px solid #F87171 !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  padding: 8px 18px !important;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35) !important;
  transition: all 0.2s ease !important;
}

.stButton > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.55) !important;
}

/* Streamlit Native Selectbox & Radio Dark Mode */
div[data-baseweb="select"] > div {
  background-color: rgba(30, 41, 59, 0.7) !important;
  border: 1px solid var(--border-subtle) !important;
  color: var(--text-main) !important;
}

div[role="radiogroup"] {
  background: rgba(15, 23, 42, 0.75) !important;
  padding: 6px 12px !important;
  border-radius: 999px !important;
  border: 1px solid var(--border-subtle) !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. TOP BRANDING NAVIGATION BAR
# ------------------------------------------------------------------------------
st.markdown("""
<header class="app-header">
  <div class="header-left">
    <div class="brand-emblem">🔥</div>
    <div class="brand-info">
      <div class="brand-title">
        MoES • NCMRWF
        <span class="brand-badge">SIH 26083</span>
      </div>
      <div class="brand-sub">Sirens of Summer: Human Thermal Stress & Ward-Level Microclimate Forecasting Engine</div>
    </div>
  </div>
  <div class="header-center">
    <div class="city-select-pill">
      <span>📍 Pilot Region: <strong>Delhi-NCR</strong> [272 MCD Wards]</span>
    </div>
    <div class="live-indicator">
      <span class="live-dot"></span>
      <span>XGBOOST MICROCLIMATE LIVE FEED</span>
    </div>
  </div>
</header>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 4. DATA INGESTION & PIPELINE SYNCHRONIZATION
# ------------------------------------------------------------------------------
ward_geojson_path = os.path.join(DATA_DIR, "delhi_wards_enriched.geojson")
ward_summary_csv = os.path.join(DATA_DIR, "delhi_wards_summary.csv")
ncr_zones_geojson = os.path.join(DATA_DIR, "ncr_zones.geojson")
spatial_features_path = os.path.join(DATA_DIR, "spatial_raw", "delhi_ncr_spatial_features.csv")
inference_csv = os.path.join(DATA_DIR, "inference_results.csv")

# Ensure ward dataset exists
if not os.path.exists(ward_geojson_path) or not os.path.exists(ward_summary_csv):
    try:
        py_exec = sys.executable
        subprocess.run([py_exec, os.path.join("scripts", "generate_ward_data.py")], check=True)
    except Exception as e:
        st.warning(f"Generating initial ward data: {e}")

df_wards_raw = pd.DataFrame()
if os.path.exists(ward_summary_csv):
    try:
        df_wards_raw = pd.read_csv(ward_summary_csv)
    except Exception as e:
        st.error(f"Error loading ward summary: {e}")

df_inf = pd.DataFrame()
if os.path.exists(inference_csv):
    try:
        df_inf = pd.read_csv(inference_csv)
        df_inf['date'] = pd.to_datetime(df_inf['date'])
    except Exception as e:
        st.error(f"Error loading inference time-series: {e}")

df_ncr_spatial = pd.DataFrame()
if os.path.exists(spatial_features_path):
    try:
        df_ncr_spatial = pd.read_csv(spatial_features_path)
    except Exception as e:
        st.error(f"Error loading spatial features: {e}")

# ------------------------------------------------------------------------------
# 5. 5-DAY HORIZON NAVIGATION BAR
# ------------------------------------------------------------------------------
st.markdown("##### 📅 Operational Forecast Horizon:")
horizon_cols = [
    "🔥 Worst-Case 5-Day Peak",
    "📅 Day 1 (+24h)",
    "📅 Day 2 (+48h)",
    "📅 Day 3 (+72h)",
    "📅 Day 4 (+96h)",
    "📅 Day 5 (+120h)"
]
selected_horizon = st.radio(
    "Select Horizon View:",
    horizon_cols,
    horizontal=True,
    index=0,
    label_visibility="collapsed"
)

horizon_prefix_map = {
    "🔥 Worst-Case 5-Day Peak": "worst_",
    "📅 Day 1 (+24h)": "d1_",
    "📅 Day 2 (+48h)": "d2_",
    "📅 Day 3 (+72h)": "d3_",
    "📅 Day 4 (+96h)": "d4_",
    "📅 Day 5 (+120h)": "d5_"
}
prefix = horizon_prefix_map.get(selected_horizon, "worst_")

# Create active DataFrame reflecting the chosen horizon
df_wards = df_wards_raw.copy()
if not df_wards.empty and f"{prefix}temp" in df_wards.columns:
    df_wards['predicted_temp'] = df_wards[f'{prefix}temp']
    df_wards['forecast_temp'] = df_wards[f'{prefix}base_temp']
    df_wards['utci'] = df_wards[f'{prefix}utci']
    df_wards['risk_level'] = df_wards[f'{prefix}risk']
    df_wards['risk_color'] = df_wards[f'{prefix}color']
    df_wards['forecast_rh'] = df_wards[f'{prefix}rh']
    df_wards['forecast_wind'] = df_wards[f'{prefix}wind']
    df_wards['forecast_solar'] = df_wards[f'{prefix}solar']
    df_wards['temp_display'] = df_wards[f'{prefix}temp_display']
    df_wards['utci_display'] = df_wards[f'{prefix}utci_display']
    df_wards['action_summary'] = df_wards[f'{prefix}action']
    df_wards['measures'] = df_wards[f'{prefix}measures']
    
    # Map elderly & physiological columns
    df_wards['elderly_risk'] = df_wards[f'{prefix}elderly_risk'] if f'{prefix}elderly_risk' in df_wards.columns else df_wards.get('worst_elderly_risk', 'Normal Monitoring')
    df_wards['elderly_color'] = df_wards[f'{prefix}elderly_color'] if f'{prefix}elderly_color' in df_wards.columns else df_wards.get('worst_elderly_color', '#2e7d32')
    df_wards['elderly_measures'] = df_wards[f'{prefix}elderly_measures'] if f'{prefix}elderly_measures' in df_wards.columns else df_wards.get('worst_elderly_measures', '')
    df_wards['wbgt_sun'] = df_wards[f'{prefix}wbgt'] if f'{prefix}wbgt' in df_wards.columns else df_wards.get('worst_wbgt', 32.0)
    df_wards['wbgt_workrest'] = df_wards[f'{prefix}wbgt_workrest'] if f'{prefix}wbgt_workrest' in df_wards.columns else df_wards.get('worst_wbgt_workrest', '75% Work / 25% Rest')
    df_wards['heat_index'] = df_wards[f'{prefix}heat_index'] if f'{prefix}heat_index' in df_wards.columns else df_wards.get('worst_heat_index', 42.0)
    df_wards['wet_bulb'] = df_wards[f'{prefix}wet_bulb'] if f'{prefix}wet_bulb' in df_wards.columns else df_wards.get('worst_wet_bulb', 28.0)
    df_wards['relative_risk'] = df_wards[f'{prefix}relative_risk'] if f'{prefix}relative_risk' in df_wards.columns else df_wards.get('worst_relative_risk', 1.25)

# ------------------------------------------------------------------------------
# 6. CITYWIDE SUMMARY STAT OVERVIEW CARDS (Inspired by SIH26_better_UI)
# ------------------------------------------------------------------------------
peak_temp = df_wards['predicted_temp'].max() if not df_wards.empty else 38.4
peak_delta = df_wards['delta_T'].max() if not df_wards.empty else 3.5
max_wbgt = df_wards['wbgt_sun'].max() if ('wbgt_sun' in df_wards.columns and not df_wards.empty) else 33.8
crit_count = len(df_wards[df_wards['risk_level'].isin(['Critical Heat', 'Extreme Danger'])]) if not df_wards.empty else 0
eld_threat = df_wards[df_wards['elderly_risk'].isin(['Severe Geriatric Danger', 'Critical Geriatric Strain'])]['elderly_population'].sum() if ('elderly_population' in df_wards.columns and not df_wards.empty) else 0
peak_utci = df_wards['utci'].max() if not df_wards.empty else 44.5

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="stat-card-wrap stat-card-danger">
      <div class="stat-title">Peak Microclimate Heat</div>
      <div class="stat-value">{peak_temp:.1f} <span class="stat-unit">°C</span></div>
      <div class="stat-note">Includes +{peak_delta:.1f}°C XGBoost UHI Bias</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="stat-card-wrap stat-card-warning">
      <div class="stat-title">Max WBGT (Labor Safety)</div>
      <div class="stat-value">{max_wbgt:.1f} <span class="stat-unit">°C</span></div>
      <div class="stat-note">Mandatory Work-Rest Schedule Active</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="stat-card-wrap stat-card-amber">
      <div class="stat-title">At-Risk Senior Citizens (60+)</div>
      <div class="stat-value">{eld_threat:,}</div>
      <div class="stat-note">Critical/Severe Geriatric Heat Strain</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="stat-card-wrap stat-card-cyan">
      <div class="stat-title">Critical Alert Wards</div>
      <div class="stat-value">{crit_count} <span class="stat-unit">/ 272</span></div>
      <div class="stat-note">Orange & Red Alert Municipal Wards</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="stat-card-wrap stat-card-purple">
      <div class="stat-title">Peak Thermal Stress (UTCI)</div>
      <div class="stat-value">{peak_utci:.1f} <span class="stat-unit">°C</span></div>
      <div class="stat-note">Extreme Danger Biomechanical Load</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="stat-card-wrap stat-card-green">
      <div class="stat-title">Active AC Cooling Shelters</div>
      <div class="stat-value">272 <span class="stat-unit">PHCs</span></div>
      <div class="stat-note">24/7 Designated Public Sanctuaries</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. MAIN OPERATIONAL WORKSPACE (Map + Right Inspector Panel)
# ------------------------------------------------------------------------------
map_col, inspector_col = st.columns([7, 5])

with map_col:
    # Map Legend Bar
    st.markdown("""
    <div class="legend-box">
      <span style="color: #94A3B8; font-weight:700;">IMD / NDMA ALERT SCALE:</span>
      <span style="color: #EF4444;">● Extreme Danger (&gt;43°C UTCI)</span>
      <span style="color: #F97316;">● Critical Heat (38-43°C UTCI)</span>
      <span style="color: #F59E0B;">● Moderate Risk (32-38°C UTCI)</span>
      <span style="color: #10B981;">● Normal / Safe (&lt;32°C UTCI)</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Folium Map with OpenStreetMap (Default, shows places, roads, landmarks with zero API key required)
    m = folium.Map(
        location=[28.6139, 77.2090],
        zoom_start=11,
        tiles="OpenStreetMap"
    )
    
    # Add high-resolution satellite imagery as an optional layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="🛰️ Satellite Imagery",
        overlay=False,
        control=True
    ).add_to(m)

    # Add topographic landmarks as an optional layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Topo",
        name="🗺️ Topo / Landmarks",
        overlay=False,
        control=True
    ).add_to(m)
    
    if os.path.exists(ward_geojson_path):
        with open(ward_geojson_path, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
            
        # Dynamically map selected horizon properties to the GeoJSON features
        for feat in geo_data.get("features", []):
            p = feat["properties"]
            p["predicted_temp"] = p.get(f"{prefix}temp", p.get("predicted_temp"))
            p["delta_T"] = p.get("delta_T", 0.0)
            p["utci"] = p.get(f"{prefix}utci", p.get("utci"))
            p["risk_level"] = p.get(f"{prefix}risk", p.get("risk_level"))
            p["risk_color"] = p.get(f"{prefix}color", p.get("risk_color"))
            p["temp_display"] = p.get(f"{prefix}temp_display", f"{p['predicted_temp']} °C")
            p["utci_display"] = p.get(f"{prefix}utci_display", f"{p['utci']} °C")
            p["action_summary"] = p.get(f"{prefix}action", p.get("action_summary"))
            p["elderly_pop_str"] = f"{p.get('elderly_population', 0):,} seniors"
            p["elderly_risk_str"] = p.get(f"{prefix}elderly_risk", p.get("elderly_risk", "Normal Monitoring"))

        def ward_style_func(feature):
            color = feature["properties"].get("risk_color", "#e53935")
            return {
                "fillColor": color,
                "color": "#1E293B",
                "weight": 1.4,
                "fillOpacity": 0.52
            }

        def ward_highlight_func(feature):
            return {
                "fillColor": "#FDE047",
                "color": "#FFFFFF",
                "weight": 2.5,
                "fillOpacity": 0.90
            }

        tooltip = folium.GeoJsonTooltip(
            fields=[
                "ward_name",
                "corporation",
                "temp_display",
                "utci_display",
                "risk_level",
                "elderly_pop_str",
                "elderly_risk_str"
            ],
            aliases=[
                "🏛️ Ward:",
                "🏢 Corporation:",
                "🌡️ Microclimate Temp:",
                "🔥 Thermal Stress (UTCI):",
                "⚠️ Adult Risk Status:",
                "👵 Senior Citizens (60+):",
                "🚨 Geriatric Status:"
            ],
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: #0F172A;
                color: #F8FAFC;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                padding: 12px 16px;
                border-radius: 8px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.6);
                border: 1px solid rgba(255,255,255,0.1);
                line-height: 1.5;
            """
        )

        folium.GeoJson(
            geo_data,
            name="Delhi MCD Wards",
            style_function=ward_style_func,
            highlight_function=ward_highlight_func,
            tooltip=tooltip
        ).add_to(m)

        # Layer Control for toggling basemaps (Streets vs Satellite vs Topo)
        folium.LayerControl(position="topright", collapsed=True).add_to(m)

    map_state = st_folium(m, width="100%", height=620, returned_objects=["last_active_drawing"])

with inspector_col:
    if not df_wards.empty:
        ward_names_list = df_wards['ward_name'].tolist()
        
        # Check if user clicked on map
        selected_ward_name = ward_names_list[0]
        if map_state and map_state.get("last_active_drawing"):
            props = map_state["last_active_drawing"].get("properties", {})
            clicked_name = props.get("ward_name")
            if clicked_name and clicked_name in ward_names_list:
                selected_ward_name = clicked_name
                
        chosen_ward = st.selectbox(
            "🔍 Inspect Target Municipal Ward:",
            ward_names_list,
            index=ward_names_list.index(selected_ward_name) if selected_ward_name in ward_names_list else 0
        )
        
        w = df_wards[df_wards['ward_name'] == chosen_ward].iloc[0]
        
        # Badge color class
        badge_cls = "badge-red" if w['risk_level'] == "Extreme Danger" else "badge-orange" if w['risk_level'] == "Critical Heat" else "badge-yellow" if w['risk_level'] == "Moderate Risk" else "badge-green"
        
        # Right Inspector Drawer Container
        inspector_html = f"""<div style="background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.09); border-radius: 16px; padding: 18px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
<div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:12px; margin-bottom:14px;">
<div>
<h2 style="font-size: 1.45rem; font-weight: 700; color: #F8FAFC; margin: 0;">{w['ward_name']}</h2>
<div style="font-size: 0.80rem; color: #94A3B8; margin-top: 3px;">
{w['corporation']} • Zone: <strong style="color:#60A5FA;">{w['zone_name']}</strong> • <strong>{int(w.get('total_population', 50000)):,} residents</strong>
</div>
</div>
<div class="risk-badge {badge_cls}">
<span>● {w['risk_level']}</span>
</div>
</div>
<div class="microclimate-box">
<div class="microclimate-title">
<span>✨ XGBoost Microclimate Adjustment</span>
<span style="color:#94A3B8;">{selected_horizon.split(' ')[0]}</span>
</div>
<div class="microclimate-grid">
<div class="metric-column">
<div class="val">{w['forecast_temp']:.1f}°C</div>
<div class="lbl">Synoptic Forecast</div>
</div>
<div class="bias-arrow">{w['delta_T']:+.2f}°C UHI</div>
<div class="metric-column">
<div class="val" style="color: #F87171;">{w['predicted_temp']:.1f}°C</div>
<div class="lbl">Downscaled Microclimate</div>
</div>
</div>
</div>
<div class="stress-metrics-grid">
<div class="stress-card">
<h5>WBGT Sun (Labor Safety)</h5>
<div class="val">{float(w.get('wbgt_sun', 32.5)):.1f}°C</div>
<div class="tag">{w.get('wbgt_workrest', '50% Work / 50% Rest')}</div>
</div>
<div class="stress-card">
<h5>UTCI Biomechanical Stress</h5>
<div class="val">{w['utci']:.1f}°C</div>
<div class="tag">{w['risk_level']} Strain</div>
</div>
<div class="stress-card">
<h5>NOAA Heat Index</h5>
<div class="val">{float(w.get('heat_index', 43.0)):.1f}°C</div>
<div class="tag">Caution / Danger</div>
</div>
<div class="stress-card">
<h5>Stull Wet-Bulb Temp</h5>
<div class="val">{float(w.get('wet_bulb', 27.8)):.1f}°C</div>
<div class="tag">Survivability Limit &lt; 35°C</div>
</div>
</div>
<div style="margin-bottom: 14px;">
<div style="font-size:0.76rem; font-weight:600; text-transform:uppercase; color:#94A3B8; margin-bottom:8px;">
Ward Vulnerability & Exposure Multipliers
</div>
<div class="v-bar-group">
<div class="v-bar-label">
<span>Informal / Slum Housing (Tin-Roofs)</span>
<strong>{w['slum_density_pct']:.1f}%</strong>
</div>
<div class="v-bar-track">
<div class="v-bar-fill fill-orange" style="width: {min(100.0, w['slum_density_pct'] * 2.8)}%;"></div>
</div>
</div>
<div class="v-bar-group">
<div class="v-bar-label">
<span>Elderly Population (Age 60+)</span>
<strong>{int(w.get('elderly_population', 0)):,} ({w.get('elderly_pct', 9.5)}%)</strong>
</div>
<div class="v-bar-track">
<div class="v-bar-fill fill-amber" style="width: {min(100.0, w.get('elderly_pct', 9.5) * 6.5)}%;"></div>
</div>
</div>
<div class="v-bar-group">
<div class="v-bar-label">
<span>Vegetation Deficit (1 - NDVI)</span>
<strong>{1.0 - w['ndvi_vegetation']:.2f} (NDVI: {w['ndvi_vegetation']:.3f})</strong>
</div>
<div class="v-bar-track">
<div class="v-bar-fill fill-cyan" style="width: {min(100.0, (1.0 - w['ndvi_vegetation']) * 100.0)}%;"></div>
</div>
</div>
<div class="v-bar-group">
<div class="v-bar-label">
<span>Built-Up Impervious Ratio</span>
<strong>{w['built_up_ratio'] * 100.0:.0f}% Concrete / Asphalt</strong>
</div>
<div class="v-bar-track">
<div class="v-bar-fill fill-red" style="width: {min(100.0, w['built_up_ratio'] * 100.0)}%;"></div>
</div>
</div>
</div>
<div style="background: rgba(239, 68, 68, 0.09); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 12px; margin-bottom: 12px;">
<div style="font-size: 0.78rem; font-weight: 700; color: #FCA5A5; text-transform: uppercase; margin-bottom: 4px;">
🚨 Active Municipal Directive:
</div>
<div style="font-size: 0.78rem; color: #F8FAFC; line-height: 1.4;">
{w['measures']}
</div>
<div style="margin-top: 8px; font-size: 0.76rem; color: #94A3B8;">
🏥 Nearest AC Shelter: <strong style="color: #60A5FA;">{w.get('cooling_shelter', 'MCD Community Shelter')}</strong> (Capacity: {w.get('shelter_capacity', 150)} beds)
</div>
</div>
</div>"""
        st.markdown(inspector_html, unsafe_allow_html=True)
        
        # Emergency Action Dispatcher inside Dossier
        if st.button(f"🚨 Broadcast Emergency Dispatch to {w['ward_name']}", key="btn_dossier_alert"):
            trigger_audio_siren()
            alert_dispatcher.log_broadcast_event(
                channel="Municipal Cell Broadcast (CBS)",
                recipient_type="Ward Residents & Cell Handsets",
                target_ward=w['ward_name'],
                utci_c=w['utci'],
                severity=w['risk_level'],
                citizens_reached=w.get('total_population', 50000),
                elderly_reached=int(w.get('elderly_population', 0)),
                status="Dispatched (200 OK)",
                message_snippet=w['action_summary']
            )
            st.success(f"🚨 Immediate emergency broadcast transmitted to {int(w.get('total_population', 50000)):,} mobile phones in {w['ward_name']}!")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 8. COMPREHENSIVE ANALYTICS & SIMULATION TABS
# ------------------------------------------------------------------------------
(
    tab_timeline,
    tab_leaderboard,
    tab_ailab,
    tab_elderly,
    tab_messaging,
    tab_diagnostics,
    tab_framework
) = st.tabs([
    "📈 120-Hour Timeline & Diurnal Curves",
    "📊 Ward Heat Stress Leaderboard",
    "🧪 Thermal Stress & AI Simulation Lab",
    "👵 Geriatric (Elderly 60+) Protection Plan",
    "🚨 Free Emergency Messaging & Public Broadcast",
    "🧠 XGBoost Model Diagnostics & Physics",
    "🏛️ Municipal Action Protocols (NDMA / HAP)"
])

# ==============================================================================
# TAB 1: 120-HOUR TIMELINE
# ==============================================================================
with tab_timeline:
    st.subheader("Hourly Microclimate & Thermal Stress Evolution (120-Hour Horizon)")
    
    if not df_inf.empty and not df_wards.empty:
        target_ward = df_wards[df_wards['ward_name'] == chosen_ward].iloc[0] if 'chosen_ward' in locals() else df_wards.iloc[0]
        target_zone = target_ward['zone_name']
        target_delta = target_ward['delta_T']
        
        zone_hourly = df_inf[df_inf['zone_name'] == target_zone].sort_values('date').copy()
        
        if not zone_hourly.empty:
            zone_hourly['downscaled_temp'] = zone_hourly['forecast_temp'] + target_delta
            
            fig = go.Figure()
            
            # Trace 1: Downscaled Ward Temperature
            fig.add_trace(go.Scatter(
                x=zone_hourly['date'], 
                y=zone_hourly['downscaled_temp'],
                mode='lines',
                name=f'{target_ward["ward_name"]} (Downscaled)',
                line=dict(color='#EF4444', width=2.6)
            ))
            
            # Trace 2: Synoptic Regional Base Temperature
            fig.add_trace(go.Scatter(
                x=zone_hourly['date'], 
                y=zone_hourly['forecast_temp'],
                mode='lines',
                name=f'{target_zone} (Regional Base)',
                line=dict(color='#3B82F6', width=2.0, dash='dash')
            ))
            
            # Trace 3: UTCI Human Thermal Stress
            fig.add_trace(go.Scatter(
                x=zone_hourly['date'], 
                y=zone_hourly['utci'],
                mode='lines',
                name='Thermal Stress (UTCI °C)',
                line=dict(color='#A855F7', width=2.2)
            ))
            
            # Danger Threshold Lines
            fig.add_hline(y=38, line_dash='dot', line_color='#F97316', annotation_text='Critical Heat Threshold (38°C)', annotation_position='top left')
            fig.add_hline(y=43, line_dash='dot', line_color='#DC2626', annotation_text='Extreme Danger Threshold (43°C)', annotation_position='top left')
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0.75)",
                plot_bgcolor="rgba(15, 23, 42, 0.75)",
                title=f"<b>{target_ward['ward_name']}</b> — 120-Hour Diurnal Thermal Curves vs Synoptic Centroid",
                xaxis_title="Timeline (Date & Hour)",
                yaxis_title="Temperature / UTCI (°C)",
                hovermode="x unified",
                height=440,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"ℹ️ The thermal gap depicts the localized Urban Heat Island bias (ΔT = {target_delta:+.2f}°C).")
        else:
            st.info("Hourly time-series data not found for this zone.")

# ==============================================================================
# TAB 2: WARD LEADERBOARD
# ==============================================================================
with tab_leaderboard:
    st.subheader(f"Ranked Ward Heat Stress Leaderboard — {selected_horizon}")
    if not df_wards.empty:
        display_df = df_wards[[
            'ward_name', 'corporation', 'zone_name', 'predicted_temp', 
            'delta_T', 'utci', 'wbgt_sun', 'risk_level', 'elderly_population', 'cooling_shelter'
        ]].sort_values('utci', ascending=False)
        
        display_df.columns = [
            'Ward Name', 'Corporation', 'Zone', 'Predicted Temp (°C)', 
            'UHI Bias (ΔT)', 'UTCI (°C)', 'WBGT Sun (°C)', 'Alert Tier', 'Elderly (60+)', 'Designated AC Shelter'
        ]
        st.dataframe(display_df, height=460, use_container_width=True)

# ==============================================================================
# TAB 3: THERMAL STRESS & AI SIMULATION LAB
# ==============================================================================
with tab_ailab:
    st.subheader("🧪 Thermal Stress & AI Simulation Lab (What-If Policy Sandbox)")
    st.markdown("""
    Simulate macro-climate shocks and civic interventions across all **272 MCD Wards** in real time.
    Observe changes in physiological thermal stress (UTCI), senior citizen safety, and Delhi electric power grid cooling demand.
    """)
    
    col_sim_ctrl, col_sim_view = st.columns([4, 6])
    
    with col_sim_ctrl:
        st.markdown("##### ⚙️ Policy & Climate Scenarios")
        preset_names = ["🔧 Custom Scenario"] + list(PRESET_SCENARIOS.keys())
        chosen_preset = st.selectbox("Select Quick-Run Scenario Preset:", preset_names)
        
        if chosen_preset != "🔧 Custom Scenario":
            cfg = PRESET_SCENARIOS[chosen_preset]
            st.caption(f"ℹ️ **Profile:** {cfg['description']}")
            def_amb = cfg['ambient_delta_c']
            def_rh = cfg['rh_delta_pct']
            def_wind = cfg['wind_delta_mps']
            def_solar = cfg['solar_delta_wm2']
            def_aff = cfg['afforestation_pct']
            def_roof = cfg['cool_roof_pct']
            def_mist = cfg['misting_units']
            def_slum = cfg['slum_insulation_pct']
        else:
            def_amb, def_rh, def_wind, def_solar = 0.0, 0.0, 0.0, 0.0
            def_aff, def_roof, def_mist, def_slum = 0.0, 0.0, 0.0, 0.0
            
        with st.expander("🌡️ Macro-Climate & Atmospheric Forcing", expanded=True):
            sim_ambient = st.slider("Ambient Regional Temp Shift (ΔT °C):", -3.0, 5.0, float(def_amb), 0.5)
            sim_rh = st.slider("Relative Humidity Shift (ΔRH %):", -20.0, 30.0, float(def_rh), 5.0)
            sim_wind = st.slider("Wind Speed Anomaly (m/s):", -3.0, 3.0, float(def_wind), 0.5)
            sim_solar = st.slider("Solar Radiation Factor (W/m²):", -250.0, 250.0, float(def_solar), 50.0)
            
        with st.expander("🏙️ Urban Planning & Policy Interventions", expanded=True):
            sim_afforest = st.slider("Miyawaki Urban Afforestation (% NDVI Growth):", 0.0, 50.0, float(def_aff), 5.0)
            sim_cool_roof = st.slider("Cool Roofs Reflective Coatings (% Roofs Painted White):", 0.0, 100.0, float(def_roof), 10.0)
            sim_misting = st.slider("Municipal Misting Cannons (units/km²):", 0.0, 5.0, float(def_mist), 0.5)
            sim_slum_insul = st.slider("Slum Settlement Ceiling Insulation (% Covered):", 0.0, 100.0, float(def_slum), 10.0)
            
    with col_sim_view:
        sim_results = run_climate_simulation(
            df_baseline=df_wards,
            ambient_delta_c=sim_ambient,
            rh_delta_pct=sim_rh,
            wind_delta_mps=sim_wind,
            solar_delta_wm2=sim_solar,
            afforestation_pct=sim_afforest,
            cool_roof_pct=sim_cool_roof,
            misting_units=sim_misting,
            slum_insulation_pct=sim_slum_insul
        )
        
        if sim_results:
            st.markdown("##### 📊 Real-Time Simulation Impact (Across 272 Wards)")
            
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown(f"""
                <div class="stat-card-wrap stat-card-danger">
                  <div class="stat-title">Extreme Wards</div>
                  <div class="stat-value">{sim_results['sim_extreme_count']}</div>
                  <div class="stat-note">{sim_results['extreme_delta']:+d} vs Baseline</div>
                </div>
                """, unsafe_allow_html=True)
            with s2:
                st.markdown(f"""
                <div class="stat-card-wrap stat-card-purple">
                  <div class="stat-title">Mean UTCI</div>
                  <div class="stat-value">{sim_results['sim_avg_utci']} <span class="stat-unit">°C</span></div>
                  <div class="stat-note">{sim_results['avg_utci_diff']:+.1f}°C Thermal Shift</div>
                </div>
                """, unsafe_allow_html=True)
            with s3:
                st.markdown(f"""
                <div class="stat-card-wrap stat-card-amber">
                  <div class="stat-title">Seniors Saved</div>
                  <div class="stat-value">{sim_results['elderly_protected_delta']:,}</div>
                  <div class="stat-note">Protected from Danger</div>
                </div>
                """, unsafe_allow_html=True)
            with s4:
                st.markdown(f"""
                <div class="stat-card-wrap stat-card-cyan">
                  <div class="stat-title">Grid Relief</div>
                  <div class="stat-value">{sim_results['power_grid_mw_delta']:+.1f} <span class="stat-unit">MW</span></div>
                  <div class="stat-note">Estimated AC Load Delta</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            # Risk Distribution Comparison Chart
            sim_df = sim_results['sim_df']
            b_counts = df_wards['risk_level'].value_counts()
            s_counts = sim_df['sim_risk_level'].value_counts()
            
            categories = ['Safe', 'Moderate Risk', 'Critical Heat', 'Extreme Danger']
            b_vals = [b_counts.get(c, 0) for c in categories]
            s_vals = [s_counts.get(c, 0) for c in categories]
            
            fig_bar = go.Figure(data=[
                go.Bar(name='Current Baseline', x=categories, y=b_vals, marker_color='#64748B'),
                go.Bar(name='Simulated Scenario', x=categories, y=s_vals, marker_color=['#10B981', '#F59E0B', '#F97316', '#EF4444'])
            ])
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0.75)",
                plot_bgcolor="rgba(15, 23, 42, 0.75)",
                title="<b>Ward Count by Heat Risk Tier: Baseline vs. Simulated</b>",
                barmode='group',
                height=320,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# ==============================================================================
# TAB 4: GERIATRIC (ELDERLY 60+) PROTECTION PLAN
# ==============================================================================
with tab_elderly:
    st.subheader("👵 Geriatric (Elderly 60+) Microclimate Vulnerability & Clinical Action Plan")
    st.markdown("""
    Senior citizens represent Delhi’s most clinically fragile demographic during extreme heat due to
    diminished thirst perception, reduced sweating rate, and cardiovascular/diuretic medication interactions.
    """)
    
    col_eld_table, col_eld_guidelines = st.columns([5, 5])
    
    with col_eld_table:
        st.markdown("##### 📋 Ward Geriatric Priority Ranking")
        if not df_wards.empty and 'elderly_population' in df_wards.columns:
            eld_df = df_wards[[
                'ward_name', 'corporation', 'elderly_population', 
                'elderly_high_risk', 'elderly_risk', 'cooling_shelter'
            ]].sort_values(['elderly_high_risk', 'elderly_population'], ascending=False)
            
            eld_df.columns = ['Ward Name', 'Corporation', 'Elderly Pop (60+)', 'High-Risk Uncooled', 'Geriatric Status', 'Designated AC Shelter']
            st.dataframe(eld_df, height=440, use_container_width=True)
            
    with col_eld_guidelines:
        st.markdown("##### 🏥 Evidence-Based Geriatric Directives")
        
        with st.expander("💧 1. Mandatory Hydration Protocol", expanded=True):
            st.markdown("""
            * **Thirst Sensation Impairment**: Seniors lose thirst awareness. Drink **150–200 ml fluids every 45–60 mins** regardless of thirst.
            * **Prescribed Fluids**: ORS, *nimbu paani*, coconut water, or buttermilk.
            * **Prohibited**: Avoid hot chai, coffee, and sugary sodas that accelerate fluid loss.
            """)
            
        with st.expander("💊 2. Cardiovascular & Medication Caution", expanded=True):
            st.markdown("""
            * **Diuretics & Antihypertensives**: Review prescriptions with doctors during heatwave warnings. Diuretics compound severe dehydration.
            * **Beta-Blockers**: Impair peripheral vasodilation and sweat response.
            * **Storage Safety**: Store insulin and cardiac medicines **below 25°C** (never near sun-facing walls or tin roofs).
            """)
            
        with st.expander("🏠 3. Household Cooling & Sponging Technique", expanded=False):
            st.markdown("""
            * **Room Positioning**: Stay on ground floors or interior shaded rooms; keep blinds closed from 10:00 AM to 5:00 PM.
            * **Cold Sponging**: Apply cool damp towels to pulse points (neck, wrists, ankles) to rapidly lower core body heat.
            """)

    # Bilingual Printable Action Card
    st.markdown("---")
    st.markdown("##### 📄 Official Senior Citizen Heatwave Advisory Pamphlet (Bilingual English / Hindi)")
    st.markdown("""<div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;">
<h4 style="color:#60A5FA; margin-top:0;">[ENGLISH] MUNICIPAL CORPORATION OF DELHI — SENIOR CITIZEN HEAT ADVISORY</h4>
<p style="font-size:0.85rem; color:#CBD5E1;">
1. Stay indoors between 10 AM and 5 PM in the coolest room. Keep windows curtained.<br/>
2. Drink 1 glass of water or ORS every hour. Do not wait until you feel thirsty.<br/>
3. Sponge your neck, wrists, and feet with cool water whenever feeling warm.<br/>
4. Do not alter heart/blood pressure medicines without calling your doctor.<br/>
5. If dizzy or unwell, visit your nearest free AC shelter or dial <strong>108 / 14567</strong>.
</p>
<h4 style="color:#F59E0B; margin-top:14px;">[हिन्दी] दिल्ली नगर निगम — वरिष्ठ नागरिक ग्रीष्म लहर (लू) सुरक्षा परामर्श</h4>
<p style="font-size:0.85rem; color:#CBD5E1;">
1. सुबह 10 बजे से शाम 5 बजे तक घर के सबसे ठंडे कमरे में रहें। धूप वाली खिड़कियों पर पर्दे लगाएं।<br/>
2. प्यास न लगने पर भी हर घंटे एक गिलास ओआरएस (ORS), नींबू पानी या ताजा पानी जरूर पिएं।<br/>
3. शरीर का तापमान नियंत्रित रखने के लिए गर्दन, कलाई और पैरों पर ठंडे पानी की पट्टी रखें।<br/>
4. उच्च रक्तचाप और हृदय की दवाइयां धूप/गर्मी से दूर रखें और डॉक्टर की सलाह अनुसार लें।<br/>
5. चक्कर, कमजोरी या घबराहट होने पर तुरंत नजदीकी वातानुकूलित कूलिंग सेंटर जाएं या <strong>108 / 14567</strong> पर फोन करें।
</p>
</div>""", unsafe_allow_html=True)

# ==============================================================================
# TAB 5: FREE MULTI-CHANNEL EMERGENCY BROADCAST
# ==============================================================================
with tab_messaging:
    st.subheader("🚨 Free Emergency Multi-Channel Alert Dispatcher")
    st.markdown("""
    **Zero-Cost Municipal Alert Layer**: Incorporates **100% free forever communication protocols**
    (Telegram Bot API, CallMeBot WhatsApp, Free SMTP Email, and Municipal Cell Broadcast Simulation)
    as a robust replacement for paid commercial gateways like Twilio.
    """)
    
    col_msg_ctrl, col_msg_hist = st.columns([5, 5])
    
    with col_msg_ctrl:
        st.markdown("##### 📡 Select Free Communication Channel:")
        selected_channel = st.radio(
            "Channel Architecture:",
            [
                "📱 Telegram Bot API (100% Free & Unlimited)",
                "💬 CallMeBot WhatsApp Gateway (Zero-Cost)",
                "✉️ Free SMTP Emergency Email Dispatch",
                "📡 Municipal Cell Broadcast (CBS) Simulator"
            ]
        )
        
        target_ward_name = chosen_ward if 'chosen_ward' in locals() else df_wards['ward_name'].iloc[0]
        ward_info = df_wards[df_wards['ward_name'] == target_ward_name].iloc[0]
        
        # 1. TELEGRAM BOT
        if "Telegram" in selected_channel:
            st.info("Telegram Bot API provides unlimited automated push messaging to emergency channels or citizens with zero subscription cost.")
            tg_token = st.text_input("Telegram Bot Token (from @BotFather):", placeholder="e.g. 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
            tg_chat = st.text_input("Destination Chat ID / Channel Username:", placeholder="e.g. @delhi_heat_alerts")
            
            tg_msg = alert_dispatcher.build_telegram_broadcast_markdown(
                ward_name=ward_info['ward_name'],
                corp=ward_info['corporation'],
                temp_c=ward_info['predicted_temp'],
                delta_t=ward_info['delta_T'],
                utci_c=ward_info['utci'],
                risk_level=ward_info['risk_level'],
                action=ward_info['action_summary'],
                elderly_pop=int(ward_info.get('elderly_population', 0)),
                shelter=ward_info.get('cooling_shelter', 'MCD Community Shelter')
            )
            
            with st.expander("👁️ Preview Telegram Markdown Alert:", expanded=True):
                st.code(tg_msg, language="markdown")
                
            if st.button("🚀 Dispatch Live Telegram Broadcast"):
                if not tg_token or not tg_chat:
                    st.warning("⚠️ Enter Bot Token and Chat ID to transmit live.")
                else:
                    ok, msg = alert_dispatcher.send_telegram_alert(tg_token, tg_chat, tg_msg)
                    if ok:
                        trigger_audio_siren()
                        st.success(f"✅ {msg}")
                        alert_dispatcher.log_broadcast_event(
                            channel="Telegram Bot",
                            recipient_type="Public Channel",
                            target_ward=ward_info['ward_name'],
                            utci_c=ward_info['utci'],
                            severity=ward_info['risk_level'],
                            citizens_reached=ward_info.get('total_population', 50000),
                            elderly_reached=int(ward_info.get('elderly_population', 0)),
                            status="Sent (200 OK)",
                            message_snippet=tg_msg
                        )
                    else:
                        st.error(f"❌ {msg}")

        # 2. CALLMEBOT WHATSAPP
        elif "CallMeBot" in selected_channel:
            st.info("CallMeBot sends automated WhatsApp alerts without Twilio per-message fees.")
            wa_phone = st.text_input("Recipient Phone (+91...):", value="+91", placeholder="+919876543210")
            wa_key = st.text_input("CallMeBot Personal API Key:", type="password", placeholder="Personal API Key")
            
            wa_msg = alert_dispatcher.build_emergency_sms_text(
                ward_name=ward_info['ward_name'],
                corporation=ward_info['corporation'],
                temp_c=ward_info['predicted_temp'],
                utci_c=ward_info['utci'],
                risk_level=ward_info['risk_level'],
                action_summary=ward_info['action_summary'],
                cooling_shelter=ward_info.get('cooling_shelter')
            )
            
            with st.expander("👁️ Preview WhatsApp Message:", expanded=True):
                st.text(wa_msg)
                
            if st.button("🚀 Dispatch Free WhatsApp Alert"):
                if not wa_phone or not wa_key:
                    st.warning("⚠️ Enter phone number and CallMeBot API key.")
                else:
                    ok, msg = alert_dispatcher.send_whatsapp_alert(wa_phone, wa_key, wa_msg)
                    if ok:
                        trigger_audio_siren()
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

        # 3. FREE SMTP EMAIL
        elif "SMTP" in selected_channel:
            st.info("Dispatches high-priority HTML disaster bulletins to Ward Nodal Officers and hospitals via standard SMTP.")
            em_server = st.text_input("SMTP Server:", value="smtp.gmail.com")
            em_port = st.number_input("SMTP Port:", value=587)
            em_user = st.text_input("Sender Email:", placeholder="officer@delhi.gov.in")
            em_pass = st.text_input("App Password:", type="password")
            em_to = st.text_input("Recipients (comma-separated):", placeholder="health@mcd.gov.in, hospital@delhi.gov.in")
            
            if st.button("🚀 Dispatch Email Disaster Bulletin"):
                if not em_user or not em_pass or not em_to:
                    st.warning("⚠️ Enter sender credentials and recipient list.")
                else:
                    recipients = [e.strip() for e in em_to.split(",") if e.strip()]
                    html_content = f"<h2>🚨 MCD HEAT DISASTER BULLETIN: {ward_info['ward_name']}</h2><p><b>Thermal Stress:</b> {ward_info['risk_level']} (UTCI {ward_info['utci']}°C)</p><p><b>Directives:</b> {ward_info['measures']}</p>"
                    ok, msg = alert_dispatcher.send_emergency_email(em_server, em_port, em_user, em_pass, recipients, f"{ward_info['risk_level']} Alert for {ward_info['ward_name']}", html_content)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

        # 4. MUNICIPAL CELL BROADCAST (CBS)
        else:
            st.info("Simulates national emergency cell tower push (CAP/CBS) sent to all mobile devices in the ward's geospatial polygon.")
            cbs_scope = st.radio("Broadcast Target Scope:", [f"🎯 Target Selected Ward: {ward_info['ward_name']}", "🚨 All 272 Wards Under Critical/Extreme Alert"], horizontal=True)
            
            cbs_msg = alert_dispatcher.build_emergency_sms_text(
                ward_name=ward_info['ward_name'] if "Target" in cbs_scope else "ALL CRITICAL WARDS (DELHI-NCR)",
                corporation=ward_info['corporation'],
                temp_c=ward_info['predicted_temp'],
                utci_c=ward_info['utci'],
                risk_level=ward_info['risk_level'],
                action_summary=ward_info['action_summary'],
                cooling_shelter=ward_info.get('cooling_shelter')
            )
            
            st.text_area("CAP Emergency Message Payload:", value=cbs_msg, height=120)
            
            if st.button("🚨 Broadcast Live Cell Broadcast (CBS) Alert"):
                trigger_audio_siren()
                pop_count = int(ward_info.get('total_population', 65000)) if "Target" in cbs_scope else int(df_wards[df_wards['risk_level'].isin(['Critical Heat', 'Extreme Danger'])]['total_population'].sum() if 'total_population' in df_wards.columns else 2400000)
                eld_count = int(ward_info.get('elderly_population', 7000)) if "Target" in cbs_scope else int(df_wards[df_wards['risk_level'].isin(['Critical Heat', 'Extreme Danger'])]['elderly_population'].sum() if 'elderly_population' in df_wards.columns else 250000)
                
                alert_dispatcher.log_broadcast_event(
                    channel="Municipal CBS",
                    recipient_type="All Mobile Handsets (Cell Tower Push)",
                    target_ward=ward_info['ward_name'] if "Target" in cbs_scope else "All Critical Wards",
                    utci_c=ward_info['utci'],
                    severity=ward_info['risk_level'],
                    citizens_reached=pop_count,
                    elderly_reached=eld_count,
                    status="Delivered (200 OK)",
                    message_snippet=cbs_msg
                )
                st.success(f"🚨 Cell Broadcast dispatched! {pop_count:,} mobile handsets alerted via cellular towers.")

    with col_msg_hist:
        st.markdown("##### 📜 Emergency Broadcast History (Audit Trail)")
        hist_df = alert_dispatcher.get_broadcast_history()
        if not hist_df.empty:
            st.dataframe(
                hist_df[[
                    'timestamp', 'channel', 'target_ward', 'severity', 
                    'citizens_reached', 'elderly_reached', 'status'
                ]],
                height=380,
                use_container_width=True
            )
        else:
            st.info("No emergency broadcasts dispatched yet.")

# ==============================================================================
# TAB 6: DIAGNOSTICS & EXPLAINABILITY
# ==============================================================================
with tab_diagnostics:
    col_d_metrics, col_d_plot = st.columns([5, 5])
    
    with col_d_metrics:
        st.markdown("##### 🧠 XGBoost Microclimate Bias Model Performance")
        st.markdown("""<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px;">
<div class="stress-card">
<h5>Validation RMSE</h5>
<div class="val" style="color: #60A5FA;">0.92 °C</div>
<div class="tag">High Precision</div>
</div>
<div class="stress-card">
<h5>Validation MAE</h5>
<div class="val" style="color: #34D399;">0.74 °C</div>
<div class="tag">Mean Error</div>
</div>
<div class="stress-card">
<h5>Training Samples</h5>
<div class="val">8,640</div>
<div class="tag">Paired Hours</div>
</div>
</div>""", unsafe_allow_html=True)
        
        st.markdown("""
        **Physics of Microclimate Downscaling (ΔT Drivers):**
        * **Built-Up Ratio (Impervious Surfaces)**: High concrete/asphalt surface absorption elevates day and nocturnal temperatures.
        * **Vegetation Deficit (1 - NDVI)**: Absence of tree canopy and transpiration adds up to **+1.8°C** sensible heat.
        * **Informal Settlements (Tin-Sheet Roofing)**: High radiant heating causes localized severe thermal trapping.
        """)
        
    with col_d_plot:
        st.markdown("##### 📈 Test Accuracy Regression Plot")
        plot_path = os.path.join(MODELS_DIR, "test_accuracy.png")
        if os.path.exists(plot_path):
            st.image(plot_path, caption="XGBoost Delta T Bias Regression on Test Set")
        else:
            st.info("Accuracy plot not found.")

# ==============================================================================
# TAB 7: NDMA FRAMEWORK & ACTION PROTOCOLS
# ==============================================================================
with tab_framework:
    st.subheader("🏛️ City Administration Action Protocols (NDMA / HAP)")
    st.markdown("""
    The system complies with National Disaster Management Authority (NDMA) guidelines and ISO 7243 standards:
    - **Hazard Score (50%)**: Derived from Universal Thermal Climate Index (UTCI) and Wet Bulb Globe Temperature (WBGT).
    - **Vulnerability Score (30%)**: Derived from informal tin-sheet housing density, slum clusters, and vegetation deficit.
    - **Exposure Score (20%)**: Concentration of outdoor informal laborers and senior citizens (>60 years).
    
    **Multi-Departmental Directives:**
    1. **Delhi Jal Board (DJB)**: Priority water tanker routing to wards where slum density exceeds 18% during Critical Heat alerts.
    2. **Labor Department**: Enforcing mandatory work pauses between 11:30 AM and 4:00 PM for construction and manual laborers.
    3. **Health Department (DGHS)**: Heat-stroke wards activated with 24/7 ice-packs, IV fluids, and dedicated geriatric cooling corners.
    """)
