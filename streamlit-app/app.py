# app.py - Retail Forecasting Streamlit App
# Deploy to Streamlit Community Cloud

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Retail Forecasting Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CONFIGURATION - Update these with your Databricks workspace details
# ============================================================================

DATABRICKS_HOST = "https://dbc-7e8a8bf0-dc9f.cloud.databricks.com"
# Token is stored in Streamlit secrets (NOT in code!)
DATABRICKS_TOKEN = st.secrets["databricks_token"]

# Product catalog - maps to your Model Serving endpoints
PRODUCTS = {
    "Cat1": {
        "name": "WHITE HANGING HEART T-LIGHT HOLDER",
        "sku": "85123A",
        "endpoint": "Cat1Forecast",
        "color": "#FF6B6B",
    },
    "Cat2": {
        "name": "JUMBO BAG RED RETROSPOT",
        "sku": "22423",
        "endpoint": "Cat2Forecast",
        "color": "#4ECDC4",
    },
}

# ============================================================================
# API FUNCTIONS
# ============================================================================


def get_forecast(endpoint_name, horizon):
    """
    Call Databricks Model Serving endpoint to get forecast.

    This function calls your deployed Model Serving endpoints (Cat1Forecast, Cat2Forecast)
    which internally access Delta Lake and return predictions.

    NO direct Delta Lake connection needed here!
    """
    try:
        response = requests.post(
            f"{DATABRICKS_HOST}/serving-endpoints/{endpoint_name}/invocations",
            headers={
                "Authorization": f"Bearer {DATABRICKS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"dataframe_records": [{"h": horizon}]},
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            predictions = data["predictions"]
            # Extract AutoETS forecast values
            forecast_values = [pred["AutoETS"] for pred in predictions]
            return forecast_values
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"Error calling endpoint: {str(e)}")
        return None


# ============================================================================
# BUSINESS LOGIC FUNCTIONS
# ============================================================================


def calculate_stock_recommendation(forecast, lead_time_days=14, safety_factor=1.2):
    """
    Calculate recommended stock levels based on forecast.

    This runs in Streamlit (NOT in Databricks) - just Python calculations!
    """
    lead_time_demand = sum(forecast[:lead_time_days])
    recommended_stock = int(lead_time_demand * safety_factor)
    return recommended_stock


# ============================================================================
# SIDEBAR - PRODUCT SELECTION & PARAMETERS
# ============================================================================

st.sidebar.title("📊 Retail Forecasting Engine")
st.sidebar.markdown("---")

selected_category = st.sidebar.selectbox(
    "Select Product Category",
    options=list(PRODUCTS.keys()),
    format_func=lambda x: f"{x}: {PRODUCTS[x]['name'][:30]}...",
)

product = PRODUCTS[selected_category]

# Forecast Horizon
st.sidebar.markdown("### Forecast Parameters")
horizon = st.sidebar.slider(
    "Forecast Horizon (days)", min_value=7, max_value=90, value=30, step=7
)

# What-If Scenarios
st.sidebar.markdown("---")
st.sidebar.markdown("### What-If Scenarios")

scenario_type = st.sidebar.selectbox(
    "Scenario Type",
    ["Normal", "Promotion (+30%)", "Supply Disruption", "Seasonal Peak (+50%)"],
)

if scenario_type == "Promotion (+30%)":
    adjustment_factor = 1.3
    scenario_desc = "30% demand increase due to promotional campaign"
    lead_time_days = 14
elif scenario_type == "Supply Disruption":
    adjustment_factor = 1.0
    scenario_desc = "Normal demand, but consider supply delays"
    lead_time_days = st.sidebar.slider("Lead Time (days)", 7, 30, 21)
elif scenario_type == "Seasonal Peak (+50%)":
    adjustment_factor = 1.5
    scenario_desc = "50% demand increase during seasonal peak"
    lead_time_days = 14
else:
    adjustment_factor = 1.0
    scenario_desc = "Standard business-as-usual forecast"
    lead_time_days = 14

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

st.title(f"📈 {product['name']}")
st.markdown(f"**SKU:** {product['sku']} | **Category:** {selected_category}")
st.markdown("---")

# Fetch forecast button
if st.button("🔮 Generate Forecast", type="primary", use_container_width=True):
    with st.spinner(f"Fetching {horizon}-day forecast from ML model..."):
        forecast = get_forecast(product["endpoint"], horizon)

        if forecast:
            # Apply scenario adjustment
            adjusted_forecast = [val * adjustment_factor for val in forecast]

            # Store in session state
            st.session_state["forecast"] = adjusted_forecast
            st.session_state["scenario"] = scenario_desc
            st.session_state["horizon"] = horizon
            st.session_state["product"] = product
            st.session_state["lead_time_days"] = lead_time_days
            st.session_state["scenario_type"] = scenario_type
            st.success("✅ Forecast generated successfully!")

# ============================================================================
# DISPLAY RESULTS (if forecast exists)
# ============================================================================

if "forecast" in st.session_state:
    forecast = st.session_state["forecast"]
    scenario_desc = st.session_state["scenario"]
    horizon = st.session_state["horizon"]
    product = st.session_state["product"]
    lead_time_days = st.session_state["lead_time_days"]
    scenario_type = st.session_state["scenario_type"]

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 Forecast Chart",
            "📋 Data Table",
            "🎯 Stock Recommendations",
            "💡 AI Insights",
        ]
    )

    # ========================================================================
    # TAB 1: FORECAST CHART
    # ========================================================================
    with tab1:
        st.markdown(f"### Demand Forecast - Next {horizon} Days")
        st.info(f"**Scenario:** {scenario_desc}")

        # Prepare data for chart
        dates = [
            (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, horizon + 1)
        ]
        df_forecast = pd.DataFrame({"Date": dates, "Predicted Demand": forecast})

        # Create interactive Plotly chart
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df_forecast["Date"],
                y=df_forecast["Predicted Demand"],
                mode="lines+markers",
                name="Forecast",
                line=dict(color=product["color"], width=3),
                marker=dict(size=6),
            )
        )

        # Add confidence band (simplified: ±15%)
        upper_bound = [val * 1.15 for val in forecast]
        lower_bound = [val * 0.85 for val in forecast]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=upper_bound,
                mode="lines",
                name="Upper Bound (+15%)",
                line=dict(width=0),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=lower_bound,
                mode="lines",
                name="Lower Bound (-15%)",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(255, 107, 107, 0.2)",
                showlegend=True,
            )
        )

        fig.update_layout(
            title=f"Demand Forecast: {product['name']}",
            xaxis_title="Date",
            yaxis_title="Units per Day",
            hovermode="x unified",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Daily Demand", f"{sum(forecast)/len(forecast):.1f} units")
        col2.metric("Total Demand (Period)", f"{sum(forecast):.0f} units")
        col3.metric("Peak Day Demand", f"{max(forecast):.1f} units")
        col4.metric("Minimum Day Demand", f"{min(forecast):.1f} units")

    # ========================================================================
    # TAB 2: DATA TABLE
    # ========================================================================
    with tab2:
        st.markdown("### Forecast Data Table")

        df_display = df_forecast.copy()
        df_display["Day of Week"] = pd.to_datetime(df_display["Date"]).dt.day_name()
        df_display["Cumulative Demand"] = df_display["Predicted Demand"].cumsum()

        st.dataframe(
            df_display.style.format(
                {"Predicted Demand": "{:.1f}", "Cumulative Demand": "{:.0f}"}
            ),
            use_container_width=True,
            height=400,
        )

        # Download button
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="📥 Download Forecast as CSV",
            data=csv,
            file_name=f"{product['sku']}_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    # ========================================================================
    # TAB 3: STOCK RECOMMENDATIONS
    # ========================================================================
    with tab3:
        st.markdown("### Stock Level Recommendations")

        # Calculate recommendations
        recommended_stock = calculate_stock_recommendation(forecast, lead_time_days)
        safety_stock = int(recommended_stock * 0.2)
        reorder_point = int(sum(forecast[:lead_time_days]))

        # Display recommendations
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "🎯 Recommended Order Quantity",
                f"{recommended_stock:,} units",
                help="Based on lead time demand + 20% safety buffer",
            )
            st.metric(
                "🔄 Reorder Point",
                f"{reorder_point:,} units",
                help="Trigger reorder when stock falls to this level",
            )

        with col2:
            st.metric(
                "🛡️ Safety Stock",
                f"{safety_stock:,} units",
                help="Emergency buffer to prevent stockouts",
            )
            st.metric(
                "📦 Lead Time",
                f"{lead_time_days} days",
                help="Expected time from order to delivery",
            )

        st.markdown("---")
        st.markdown("#### Inventory Timeline")

        # Inventory timeline chart
        inventory_levels = []
        current_stock = recommended_stock

        for i, daily_demand in enumerate(forecast):
            current_stock -= daily_demand
            inventory_levels.append(max(0, current_stock))

            # Reorder when below reorder point
            if current_stock < reorder_point and i >= lead_time_days:
                current_stock += recommended_stock

        fig_inv = go.Figure()

        fig_inv.add_trace(
            go.Scatter(
                x=dates,
                y=inventory_levels,
                mode="lines",
                name="Stock Level",
                line=dict(color="#2ecc71", width=3),
            )
        )

        # Add reorder point line
        fig_inv.add_hline(
            y=reorder_point,
            line_dash="dash",
            line_color="orange",
            annotation_text="Reorder Point",
        )

        # Add safety stock line
        fig_inv.add_hline(
            y=safety_stock,
            line_dash="dash",
            line_color="red",
            annotation_text="Safety Stock",
        )

        fig_inv.update_layout(
            title="Projected Inventory Levels",
            xaxis_title="Date",
            yaxis_title="Stock Units",
            height=400,
        )

        st.plotly_chart(fig_inv, use_container_width=True)

    # ========================================================================
    # TAB 4: AI INSIGHTS
    # ========================================================================
    with tab4:
        st.markdown("### 💡 AI-Powered Insights")

        # Generate insights
        avg_demand = sum(forecast) / len(forecast)
        trend = "increasing" if forecast[-1] > forecast[0] else "decreasing"
        volatility = max(forecast) - min(forecast)

        st.markdown(
            f"""
        **Forecast Summary for {product['name']}**
        
        📊 **Demand Pattern Analysis:**
        - Average daily demand: **{avg_demand:.1f} units**
        - Demand trend: **{trend}** over the forecast period
        - Volatility: **{volatility:.1f} units** (difference between peak and minimum)
        - Scenario applied: **{scenario_desc}**
        
        🎯 **Key Recommendations:**
        1. **Order {recommended_stock:,} units** to cover the next {lead_time_days} days with safety buffer
        2. **Set reorder point** at {reorder_point:,} units to avoid stockouts
        3. **Maintain safety stock** of {safety_stock:,} units for unexpected demand spikes
        
        ⚠️ **Risk Factors:**
        - {'High volatility detected - consider increasing safety stock' if volatility > avg_demand else 'Stable demand pattern - standard safety stock is sufficient'}
        - {'Increasing trend - monitor closely for potential stock acceleration' if trend == 'increasing' else 'Decreasing trend - avoid over-ordering'}
        
        💼 **Business Impact:**
        - Estimated capital tied in inventory: **₹{recommended_stock * 50:,.0f}** (assuming ₹50/unit cost)
        - Potential lost sales if understocked: **₹{reorder_point * 100:,.0f}** (assuming ₹100/unit revenue)
        """
        )

        st.info(
            """
        **Note:** These insights are generated using AutoETS forecasting model with MLflow tracking. 
        Forecasts are updated daily with latest sales data. For critical business decisions, 
        consult with procurement and operations teams.
        """
        )

else:
    # ========================================================================
    # WELCOME SCREEN (no forecast yet)
    # ========================================================================
    st.info(
        "👆 Select a product and forecast horizon from the sidebar, then click 'Generate Forecast' to begin."
    )

    st.markdown(
        """
    ## Welcome to InventoryForge
    
    This **Predictive Inventory Analytics Engine** helps you:
    - 📈 Generate accurate demand forecasts using ML models (AutoETS)
    - 🎯 Get optimal stock recommendations
    - 💡 Run what-if scenarios (promotions, disruptions, seasonal peaks)
    - 📊 Visualize demand patterns and inventory timelines
    
    ### How It Works:
    1. **Select Product:** Choose from available product categories
    2. **Set Parameters:** Adjust forecast horizon and scenario
    3. **Generate Forecast:** Click the button to get ML-powered predictions
    4. **Explore Insights:** Navigate tabs for charts, data, and recommendations
    
    ### Architecture:
    - **Data Storage:** Databricks Delta Lake
    - **ML Models:** AutoETS + Prophet (tracked in MLflow)
    - **Model Serving:** Databricks Model Serving endpoints
    - **This App:** Streamlit (calls endpoints via REST API)
    
    **No direct Delta Lake connection needed!** The Model Serving endpoints handle all data access.
    """
    )

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    "🚀 InventoryForge v1.0 | Built for Impact pSiddhi S2-D-02 | Powered by Databricks + Streamlit"
)
