# 🌡️ Sirens of Summer: Hyper-Local Microclimate Heat Alert System (Delhi-NCR)

> **Smart India Hackathon (SIH 2026)** | **Problem Statement**: Extreme Heat Early Warning & Microclimate Downscaling Engine

An AI-powered, hyper-local heat early warning system that predicts human thermal stress, urban heat island (UHI) microclimates, and physiological risk across **all 272 MCD Wards** in Delhi-NCR with a **120-hour (5-Day) forecasting horizon**.

---

## 🌟 Key Highlights & Capabilities

* **272 MCD Ward Granularity**: Downscales regional synoptic forecasts down to individual municipal wards across East, North, and South Delhi Municipal Corporations.
* **120-Hour Diurnal Evolution Timeline**: Interactive hour-by-hour time-series showing how heat builds up each afternoon and whether wards experience nocturnal cooling or dangerous heat trapping.
* **5-Day Horizon Navigation**: Interactive day-by-day navigation (`Day 1 (+24h)` through `Day 5 (+120h)`) plus a **Worst-Case 5-Day Peak** selector for disaster management planning.
* **Universal Thermal Climate Index (UTCI)**: Biomechanical heat stress calculation integrating dry-bulb temperature, mean radiant temperature ($T_r$), relative humidity, and wind speed via `pythermalcomfort` (ISO 7243 compliant).
* **🧪 AI Simulation Lab (What-If Policy Sandbox)**: Real-time interactive sandbox allowing urban planners to simulate climate shifts (ambient heat rise, wet-bulb humidity, wind stagnation) and civic interventions (cool roofs coating %, Miyawaki urban afforestation, atomized misting canons, and slum thermal insulation) with instant before-vs-after delta metrics and power grid relief estimates.
* **👵 Geriatric (Elderly 60+) Protection System**: Quantifies ward-level senior citizen demographics (~1.9M seniors across Delhi), flags high-risk uncooled tin-roof households, maps 272 designated 24/7 air-conditioned public cooling shelters, and provides clinical directives (hydration rules, cardiovascular/diuretic medication watch, bilingual English/Hindi pamphlets).
* **🚨 100% Free Multi-Channel Emergency Dispatch**: Zero-cost replacement for commercial SMS gateways like Twilio. Integrates Telegram Bot API (unlimited free push alerts), CallMeBot WhatsApp Gateway, Free SMTP Email for ward nodal officers, and NDMA-compliant Cell Broadcast Service (CBS) with Web Audio siren tones and audit logging.
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

## 🧠 Model Selection, EDA & Benchmarking Ablation Study

To mathematically validate our downscaling architecture and avoid arbitrary algorithm selection, we conducted a rigorous **Exploratory Data Analysis (EDA)** and a **Multi-Model Benchmark Matrix** comparing 5 machine learning algorithms on the 8,640 paired hourly observations of Delhi-NCR microclimates.

### 1. Exploratory Data Analysis (EDA) Insights & Feature Engineering
* **Non-Linear Diurnal Thermal Trapping**: Linear correlation between synoptic forecast and local temperature breaks down at nighttime due to radiative heat trapping. Introducing **continuous cyclical time harmonics ($\sin/\cos$ diurnal transforms)** captured the afternoon peak and nocturnal thermal lag.
* **Thermal Inertia (24-Hour Memory)**: Concrete, asphalt, and uninsulated metal roofs store heat during extreme afternoon insolation. The engineered **24-hour lag feature (`temp_lag_24h`)** captures cumulative thermal stress across multi-day heatwaves.
* **Micro-Scale Atmospheric Interactions**: High humidity paired with low wind speed suppresses evaporative cooling, exponentially increasing the microclimate bias ($\Delta T$). Tree canopy deficit (NDVI) acts as a local sensible heat multiplier.

### 2. Multi-Model Benchmark Matrix (Ablation Study)

All models were evaluated on the same 20% holdout test set using identical features (`forecast_temp`, `forecast_rh`, `forecast_wind`, `forecast_solar`, `diurnal_sin`, `diurnal_cos`, `temp_lag_24h`, `lat`, `lon`):

| Model Architecture | RMSE ($^\circ\text{C}$) | MAE ($^\circ\text{C}$) | $R^2$ Score | Inference Latency | Selection Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Ridge Regression (Linear Baseline)** | $1.4087^\circ\text{C}$ | $1.0340^\circ\text{C}$ | $0.3620$ | $0.0003\text{ ms}$ | ❌ **Rejected**: Underfits; unable to model non-linear boundary layer thermodynamics. |
| **Random Forest Regressor** | $1.1541^\circ\text{C}$ | $0.8620^\circ\text{C}$ | $0.5718$ | $0.0130\text{ ms}$ | ⚠️ **Baseline Bagging**: High variance; slower inference on embedded servers. |
| **CatBoost Regressor** | $1.1708^\circ\text{C}$ | $0.8829^\circ\text{C}$ | $0.5593$ | $0.0007\text{ ms}$ | ⚠️ **Viable**: Good handling of categorical features, but slightly higher error. |
| **LightGBM Regressor** | $1.0904^\circ\text{C}$ | $0.8238^\circ\text{C}$ | $0.6177$ | $0.0019\text{ ms}$ | 🥈 **Runner-Up**: Highly competitive accuracy and fast leaf-wise convergence. |
| **XGBoost (Chosen Production Model)** | **$1.0852^\circ\text{C}$** | **$0.8211^\circ\text{C}$** | **$0.6214$** | **$0.0011\text{ ms}$** | 🏆 **Production Champion**: Lowest error, highest $R^2$, and optimal regularization ($L_1/L_2$) against overfitting. |
| **Weighted Ensemble (XGB 45% + Cat 35% + LGB 20%)** | $1.1067^\circ\text{C}$ | $0.8367^\circ\text{C}$ | $0.6062$ | $0.0420\text{ ms}$ | ℹ️ **Ensemble Test**: Solid stability, but single XGBoost provides superior sub-millisecond edge latency with slightly better empirical error. |

> **Reproducibility**: Run `python scripts/benchmark_models.py` to re-execute the automated ablation benchmark.

---

### 3. Explainable AI (XAI) via SHAP (SHapley Additive exPlanations)

To ensure full transparency for municipal disaster response teams, we integrated **SHAP TreeExplainer** to quantify exactly how each atmospheric and physical feature influences the microclimate temperature bias ($\Delta T$):

| Feature Rank | Feature Description | Mean $|SHAP|$ Impact ($^\circ\text{C}$) | Physical & Civic Interpretation |
| :---: | :--- | :---: | :--- |
| **#1** | `forecast_temp` (Ambient Forecast) | **$1.766^\circ\text{C}$** | Sets the macro synoptic baseline; high baseline amplifies urban sensible heat exchange. |
| **#2** | `temp_lag_24h` (Thermal Memory) | **$0.581^\circ\text{C}$** | Measures heat accumulated in asphalt/masonry from the preceding day (multi-day heatwave compounding). |
| **#3** | `diurnal_cos` (Solar Cycle) | **$0.515^\circ\text{C}$** | Governs day-to-night radiative transition; drives nighttime UHI heat retention in dense wards. |
| **#4** | `forecast_rh` (Relative Humidity) | **$0.294^\circ\text{C}$** | High moisture traps re-radiated longwave heat, compounding wet-bulb physiological strain. |
| **#5** | `forecast_solar` (Solar Radiation) | **$0.230^\circ\text{C}$** | Drives direct sensible heating of unshaded roofs and open asphalt surfaces. |
| **#6** | `lat` (Spatial Latitude) | **$0.220^\circ\text{C}$** | Captures spatial gradient from rural peripheral fringes into Delhi's high-density urban core. |
| **#7** | `diurnal_sin` (Time Asymmetry) | **$0.172^\circ\text{C}$** | Models asymmetrical afternoon heating rates (steep rise at 12 PM vs slow cooling at 7 PM). |
| **#8** | `forecast_wind` (Surface Wind Speed) | **$0.085^\circ\text{C}$** | Stagnant winds ($<2\text{ m/s}$) trap heat plumes; higher wind speeds induce ventilative cooling. |
| **#9** | `lon` (Spatial Longitude) | **$0.049^\circ\text{C}$** | Secondary spatial orientation (East vs West Delhi topographical variations). |

---

### 4. Strategic Comparison: Sirens of Summer vs Proprietary Global AI Engines

| Architectural Dimension | Global AI Engines (e.g. Google GraphCast / Earth Engine) | Sirens of Summer (Our Architecture) |
| :--- | :--- | :--- |
| **Spatial Granularity** | **$0.25^\circ \times 0.25^\circ$ ($\approx 28 \text{ km} \times 28 \text{ km}$)**<br>Entire Delhi-NCR fits into just 2–3 coarse grid cells. | **Hyper-Local Sub-Kilometer (<1 km)**<br>Mapped directly to all **272 individual MCD Municipal Administrative Wards**. |
| **Urban Morphology Awareness** | ❌ **Blind to Civic Infrastructure**<br>Cannot distinguish between a shaded Lutyens' forest and a tin-roof slum in Seelampur. | ✅ **Socio-Physical Hybrid Features**<br>Directly ingests Sentinel-2 NDVI canopy deficit, DUSIB slum densities, and built-up concrete ratios. |
| **Physiological Stress Metrics** | ⚠️ Raw air temperature ($T_{\text{air}}$) only. | ✅ **ISO 7243 Compliant UTCI & WBGT**<br>Biomechanical human strain modeling for labor safety and geriatric protection. |
| **Cost & Civic Sovereignty** | ❌ **High Recurring Dollar Subscriptions**<br>Requires enterprise cloud billing, credit cards, and proprietary API lock-in. | ✅ **100% Free & Self-Hosted**<br>Runs on standard municipal edge servers with zero ongoing vendor costs. |
| **Actionable Municipal Directives** | ❌ Passive numerical predictions with no municipal protocol integration. | ✅ **Automated Civic Triggers**<br>Water tanker dispatch, 24/7 cooling shelter activation, labor work bans, and free Telegram/CBS alerts. |

---

## 📁 Repository Structure

```
SIH-26/
├── microclimate_system/
│   ├── app.py                      # Main Streamlit web application
│   ├── main.py                     # Master 6-step pipeline execution script
│   ├── config.py                   # Centralized configuration & NCR zone definitions
│   ├── ai_simulation_lab.py        # What-If policy sandbox & real-time simulation engine
│   ├── alert_dispatcher.py         # 100% Free multi-channel emergency alert service
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
│       ├── benchmark_models.py          # Multi-model ablation study & SHAP analysis
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
