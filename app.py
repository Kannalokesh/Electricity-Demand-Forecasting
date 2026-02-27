import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import plotly.graph_objects as go
from datetime import timedelta

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Grid Control Room | Kansai Electric",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* This removes the padding at the top and sides of the main container */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* This makes the chart area stretch even further */
        .stPlotlyChart {
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CACHING ASSETS ---
@st.cache_resource
def load_models():
    q10 = joblib.load('app_assets/lgbm_q10.pkl')
    q50 = joblib.load('app_assets/lgbm_q50.pkl')
    q90 = joblib.load('app_assets/lgbm_q90.pkl')
    with open('app_assets/model_features.json', 'r') as f:
        features = json.load(f)
    return q10, q50, q90, features

@st.cache_data
def load_data():
    df = pd.read_csv('app_assets/app_database.csv', parse_dates=['datetime'])
    df.set_index('datetime', inplace=True)
    return df

# Load Assets
model_q10, model_q50, model_q90, feature_cols = load_models()
data = load_data()
lower_alpha = 0.10
upper_alpha = 0.90
confidence_level = int((upper_alpha - lower_alpha) * 100)

# --- 3. UI: SIDEBAR CONTROLS ---
st.sidebar.image("https://cdn.iconscout.com/icon/free/png-256/free-apple-settings-icon-svg-download-png-493162.png?f=webp", width=50)
st.sidebar.title("System Controls")
st.sidebar.markdown("Configure the forecasting parameters")

# Date Selector
min_date = data.index.min().date()
max_date = data.index.max().date()
selected_date = st.sidebar.date_input(
    "Select Forecast Date", 
    value=min_date + timedelta(days=100), 
    min_value=min_date, 
    max_value=max_date
)

st.sidebar.markdown("---")
st.sidebar.subheader("🌡️ Simulator")
temp_modifier = st.sidebar.slider(
    "Temperature Modifier (°C)", 
    min_value=-10.0, max_value=10.0, value=0.0, step=0.5,
    help="Simulate a heatwave or cold snap."
)

st.sidebar.markdown("---")
# THE TRIGGER BUTTON
run_forecast = st.sidebar.button("🚀 Run Forecast Analysis", use_container_width=True)


# --- 4. CONDITIONAL EXECUTION ---
if run_forecast:
    # DATA PROCESSING & PREDICTION
    start_time = pd.to_datetime(selected_date)
    end_time = start_time + timedelta(days=1) - timedelta(hours=1)
    day_data = data.loc[start_time:end_time].copy()

    if len(day_data) > 0:
        # Apply Simulator Modification
        if temp_modifier != 0:
            day_data['temperature'] = day_data['temperature'] + temp_modifier
            day_data['HDD'] = np.maximum(0, 18 - day_data['temperature'])
            day_data['CDD'] = np.maximum(0, day_data['temperature'] - 24)

        # Generate Predictions
        X_predict = day_data[feature_cols]
        pred_q50 = model_q50.predict(X_predict)
        pred_q10 = np.minimum(model_q10.predict(X_predict), pred_q50)
        pred_q90 = np.maximum(model_q90.predict(X_predict), pred_q50)

        # MAIN DASHBOARD UI
        st.title("⚡ Day-Ahead Grid Demand Forecast")
        st.markdown(f"**Target Jurisdiction:** Kansai Electric Power | **Forecast Date:** {selected_date}")

        # KPI Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Peak Expected Demand", f"{int(pred_q50.max())}")
        col2.metric("Maximum Risk Demand", f"{int(pred_q90.max())}")
        col3.metric("Time of Peak Demand", day_data.index[np.argmax(pred_q90)].strftime('%H:00'))
        col4.metric("Avg Regional Temp", f"{day_data['temperature'].mean():.1f} °C")

        st.markdown("---")

        # PLOTLY CHART
        fig = go.Figure()

        # Uncertainty Band 
        fig.add_trace(go.Scatter(
            x=day_data.index.tolist() + day_data.index.tolist()[::-1],
            y=list(pred_q90) + list(pred_q10)[::-1], # Force to list
            fill='toself',
            fillcolor='rgba(255, 165, 0, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name=f'{confidence_level}% Confidence Interval',
            hoverinfo="skip"
        ))

        # Expected Prediction (Force to list to avoid the 0-line issue)
        fig.add_trace(go.Scatter(
            x=day_data.index, 
            y=list(pred_q50),
            mode='lines+markers',
            line=dict(color='darkorange', width=3),
            name='Expected Forecast (Median)'
        ))

        # 3. Actual Demand 
        actual_col = 'actual_performance(10000 kW)'
        if actual_col in day_data.columns:
            fig.add_trace(go.Scatter(
                x=day_data.index, 
                y=day_data[actual_col].tolist(), 
                mode='lines',
                line=dict(color='dodgerblue', width=2, dash='dot'),
                name='Actual System Demand'
            ))

        fig.update_layout(
            title="24-Hour Load Curve Analysis",
            xaxis_title="Time of Day",
            yaxis_title="Demand (10,000 kW)",
            hovermode="x unified",
            template="plotly_dark",
            height=600
        )

        st.plotly_chart(fig, use_column_width=True)

        # Explainability
        with st.expander("ℹ️ Model Explainability"):
            st.write("""
            This forecast uses a **LightGBM Quantile Regressor**. 
            It analyzes historical lags (24h/168h) and thermodynamic variables (HDD/CDD). 
            The orange line represents the most likely outcome, while the shaded area represents potential volatility.
            """)
            
        st.success(f"Calculated for {selected_date}")

    else:
        st.error("⚠️ No historical data available for the selected date.")

else:
    # --- 5. THE WELCOME SCREEN (Shown before clicking button) ---
    st.title("⚡ Kansai Electric: Demand Forecasting System")
    st.info("System Ready. Please configure parameters in the sidebar and click 'Run Forecast Analysis'.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        ### 📋 How to Use
        1. **Select a Target Date:** Choose a date from 2023 in the sidebar.
        2. **Weather Simulation:** (Optional) Adjust the temperature slider to simulate extreme weather.
        3. **Execute:** Click the button to run the Machine Learning model.
        
        ### 🏢 Business Impact
        This system allows grid operators to schedule power plants efficiently, reducing wasted energy and ensuring grid stability during peak loads.
        """)
    
    with col_b:
        # High quality grid-related image
        st.image("https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&q=80&w=2070", 
                 caption="Kansai Regional Infrastructure", use_column_width=True)

    st.markdown("---")
    st.subheader("🛠️ Current Model Configuration")
    st.json({
        "Algorithm": "LightGBM",
        "Objective": "Quantile Regression (0.1, 0.5, 0.9)",
        "Features": feature_cols,
        "Horizon": "24-Hours Day Ahead"
    })