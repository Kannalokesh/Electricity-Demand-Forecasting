# ⚡ Day-Ahead Electricity Demand Forecasting (Kansai Region)

An enterprise-grade Machine Learning solution for predicting regional electricity load with **2.59% MAPE** and probabilistic risk assessment.

## 📊 Business Impact
Electricity cannot be stored easily. Grid operators must perfectly balance supply and demand to avoid blackouts and minimize costs. This tool provides a **Day-Ahead Forecast** with **Uncertainty Bands**, allowing operators to schedule power plants and manage "Spinning Reserves" efficiently.

## 🎬 System Walkthrough
<!-- DRAG AND DROP YOUR VIDEO FILE HERE -->


## 🛠️ Technical Highlights
- **Architecture:** Probabilistic Quantile Regression using LightGBM.
- **Accuracy:** ACHIEVED **R²: 0.9663** and **MAPE: 2.59%**.
- **Data Leakage Fix:** Identifed and resolved critical target leakage by enforcing a strict 24h/168h lag policy and chronological TimeSeriesSplitting.
- **Feature Engineering:** Integrated Japanese Holiday calendars, Cyclical Time transforms, and Thermodynamic Degree Days (HDD/CDD).
- **Interactive Dashboard:** Built with Streamlit, featuring a **"What-If" Scenario Simulator** for temperature stress testing.

## 🚀 Installation & Usage
1. **Clone the repo:**
   ```bash
   git clone https://github.com/Kannalokesh/Electricity-Demand-Forecasting.git
   cd Electricity-Demand-Forecasting