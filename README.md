# 🌡️ Sirens of Summer: Hyper-Local Microclimate Heat Alert System (Delhi-NCR)

> **Smart India Hackathon (SIH 2026)** | **Problem Statement**: Extreme Heat Early Warning & Microclimate Downscaling Engine

An AI-powered, hyper-local heat early warning system that predicts human thermal stress, urban heat island (UHI) microclimates, and physiological risk across **all 272 MCD Wards** in Delhi-NCR with a **120-hour (5-Day) forecasting horizon**.

---

## 🌟 Key Highlights & Capabilities

* **272 MCD Ward Granularity**: Downscales regional synoptic forecasts down to individual municipal wards across East, North, and South Delhi Municipal Corporations.
* **120-Hour Diurnal Evolution Timeline**: Interactive hour-by-hour time-series showing how heat builds up each afternoon and whether wards experience nocturnal cooling or dangerous heat trapping.
* **5-Day Horizon Navigation**: Interactive day-by-day navigation (`Day 1 (+24h)` through `Day 5 (+120h)`) plus a **Worst-Case 5-Day Peak** selector for disaster management planning.
* **Universal Thermal Climate Index (UTCI)**: Biomechanical heat stress calculation integrating dry-bulb temperature, mean radiant temperature ($T_r$), relative humidity, and wind speed via `pythermalcomfort` (ISO 7243 compliant).
* **Tri-Factor Vulnerability Framework (NDMA Compliant)**:
  * **Hazard (50%)**: Physiological UTCI heat stress score.
  * **Vulnerability (30%)**: Physical proxies including DUSIB slum cluster density, tin-sheet roofing prevalence, and vegetation deficits (NDVI).
  * **Exposure (20%)**: Population density and concentration of vulnerable demographics (outdoor laborers, elderly).
* **Actionable Municipal Directives**: Automated emergency triggers per ward (dispatching water tankers, opening 24/7 cooling shelters, enforcing work-stoppages for outdoor laborers).

---

## 🏗️ System Architecture & Pipeline

```
 ┌──────────────────────┐      ┌─────────────────────────┐
 │ 1. Data Ingestion    │ ───> │ 2. Preprocessing & Lags │
 │  Open-Meteo & ERA5   │      │  Diurnal Sin/Cos & Lag  │
 └──────────────────────┘      └─────────────────────────┘
            │                               │
            ▼                               ▼
 ┌──────────────────────┐      ┌─────────────────────────┐
 │ 3. XGBoost Training  │ ───> │ 4. Real-Time Inference  │
 │  Predicts ΔT Bias    │      │  5-Day Rolling Forecast │
 └──────────────────────┘      └─────────────────────────┘
            │                               │
            ▼                               ▼
 ┌──────────────────────┐      ┌─────────────────────────┐
 │ 5. UTCI Alert Layer  │ ───> │ 6. 272 Ward Downscaling │
 │  Physiological Heat  │      │  NDVI, Slum, Built-up   │
 └──────────────────────┘      └─────────────────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ 7. Interactive UI       │
                               │  Streamlit + Folium     │
                               └─────────────────────────┘
```

1. **Data Ingestion (`data_ingestion.py`)**: Fetches 90 days of historical hourly weather data (actuals from ERA5 and forecasts from GFS Seamless) across 15 NCR centroids.
2. **Preprocessing (`preprocessing.py`)**: Computes cyclical time features ($\sin/\cos$ diurnal cycles) and 24-hour thermal inertia lags.
3. **Model Training (`train_model.py`)**: Trains an XGBoost Regressor to predict localized microclimate temperature bias ($\Delta T$) with evaluation plots.
4. **Real-Time Inference (`inference.py`)**: Queries Open-Meteo for live 120-hour forecasts and applies the trained XGBoost model to correct forecasts.
5. **Alert Layer & UTCI (`alert_layer.py`)**: Calculates physiological UTCI and flags critical threshold breaches ($38^\circ\text{C}$ Critical / $43^\circ\text{C}$ Extreme Danger).
6. **Ward Downscaling & Geospatial Synthesis (`scripts/generate_ward_data.py`)**: Combines 272 MCD ward polygons with satellite NDVI, built-up concrete ratios, and DUSIB slum densities to compute ward-specific microclimates for Days 1–5.
7. **Interactive Dashboard (`app.py`)**: Rich Folium choropleth map, ward diagnostic dossiers, and 120-hour diurnal Plotly curves.

---

## 📊 Data Sources & Provenance

| Dataset | Source | Purpose |
| :--- | :--- | :--- |
| **Numerical Weather Forecasts** | Open-Meteo GFS Seamless API | 120-hour rolling hourly temperature, humidity, wind, and solar radiation. |
| **Reanalysis Ground Truth** | ECMWF ERA5 | Ground-truth historical data for training XGBoost microclimate bias model. |
| **Ward Boundaries** | Municipal Corporation of Delhi (MCD) | 272 official administrative ward polygons in GeoJSON format. |
| **Slum & Informal Settlements** | Delhi Urban Shelter Improvement Board (DUSIB) | 841 documented slum clusters and roofing material distributions. |
| **Vegetation Deficit (NDVI)** | Sentinel-2 / Landsat Multispectral | Ward-level green cover and surface reflectance proxies. |
| **Demographics** | Census of India / WorldPop | Ward and zone-level population densities and vulnerable populations. |

---

## 📁 Repository Structure

```
SIH-26/
├── microclimate_system/
│   ├── app.py                      # Main Streamlit web application
│   ├── main.py                     # Master 6-step pipeline execution script
│   ├── config.py                   # Centralized configuration & NCR zone definitions
│   ├── data_ingestion.py           # Module 1: Historical ERA5 & GFS ingestion
│   ├── preprocessing.py            # Module 2: Feature engineering & diurnal cycles
│   ├── train_model.py              # Module 3: XGBoost training & accuracy evaluation
│   ├── inference.py                # Module 4: Real-time 5-day forecast inference
│   ├── alert_layer.py              # Module 5: UTCI heat stress computation
│   ├── requirements.txt            # Python dependencies
│   ├── data/
│   │   ├── delhi_wards_enriched.geojson # 272 MCD wards with 5-day horizon attributes
│   │   ├── delhi_wards_summary.csv      # Ward-level tabular summary
│   │   ├── inference_results.csv        # 120-hour forecast & UTCI time-series
│   │   ├── ingested_data.csv            # Raw historical training data
│   │   ├── preprocessed_data.csv        # Preprocessed features
│   │   ├── ncr_zones.geojson            # Regional NCR zone polygons
│   │   └── spatial_raw/                 # Raw ward boundaries, slum tables, and districts
│   ├── models/
│   │   ├── xgboost_model.json           # Serialized XGBoost model weights
│   │   └── test_accuracy.png            # Model test accuracy regression plot
│   └── scripts/
│       ├── download_spatial_data.py     # Automated boundary & spatial feature collector
│       └── generate_ward_data.py        # Ward-level spatial enrichment generator
├── .gitignore                      # Excludes venv, pycache, and checkpoints
├── README.md                       # Comprehensive project documentation
└── SIH-26-15.pdf                   # Problem statement & submission documents
```

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.10+** (Tested on Python 3.11)
* Git

### Installation & Setup

1. **Clone the Repository & Navigate to Directory**:
   ```bash
   git clone https://github.com/vivek-red/SIH-26.git
   cd SIH-26/microclimate_system
   ```

2. **Create and Activate a Virtual Environment**:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🏃 Running the System

### 1. Run the Complete Data & Model Pipeline
Fetches fresh historical data, retrains XGBoost, pulls live 5-day weather, and synthesizes 272 ward layers:
```bash
python main.py
```

### 2. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🌡️ Heat Stress & Alert Tiers (UTCI Standards)

| Alert Level | UTCI Range | Primary Municipal Action Directive |
| :--- | :---: | :--- |
| **Safe** | $< 32^\circ\text{C}$ | Routine municipal monitoring; standard water supply checks. |
| **Moderate Risk** | $32^\circ\text{C} - 38^\circ\text{C}$ | Mandatory hydration breaks for outdoor workers; ORS distribution at transit hubs. |
| **Critical Heat** | $38^\circ\text{C} - 43^\circ\text{C}$ | Activate public misting fans, set up cooling booths, halt non-essential outdoor work. |
| **Extreme Danger** | $\ge 43^\circ\text{C}$ | **Emergency Declaration**: Open 24/7 cooling centers, enforce complete outdoor work ban (11 AM–4 PM), dispatch emergency water tankers to slum settlements. |

---

## 👥 Team: Sirens of Summer
* **Hackathon**: Smart India Hackathon (SIH 2026)
* **Domain**: Disaster Management / AI & Climate Resilience
