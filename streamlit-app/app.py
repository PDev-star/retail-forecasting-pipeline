# InventoryForge: Predictive Retail Inventory Management System
# Purpose: Generate ML-based demand forecasts and optimal stock recommendations
# Stack: Streamlit (frontend) + FastAPI (ML backend) + MLflow (model tracking)

import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.sidebar import render_sidebar
from components.tabs import (
    render_forecast_tab,
    render_data_tab,
    render_stock_tab,
    render_insights_tab,
    render_welcome_screen,
)
from services.api_client import get_forecast
from services.inventory import calculate_stock_recommendation
from utils.config import PRODUCTS, keep_fastapi_warm

# ============================================================================
# PAGE CONFIGURATION (must be first Streamlit command)
# ============================================================================
st.set_page_config(
    page_title="InventoryForge - Retail Forecasting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Keep FastAPI warm (3 iterations, 45 sec total wait)
keep_fastapi_warm()

# ============================================================================
# MAIN APP LAYOUT
# ============================================================================

def main():
    # App title
    st.title("📊 InventoryForge: Predictive Retail Inventory Management")
    st.markdown("*Generate accurate demand forecasts and optimal stock recommendations using ML*")
    st.markdown("---")

    # Render sidebar (product selection, forecast parameters, scenarios)
    sidebar_config = render_sidebar(PRODUCTS)

    selected_category = sidebar_config["selected_category"]
    product = sidebar_config["product"]
    horizon = sidebar_config["horizon"]
    scenario_type = sidebar_config["scenario_type"]
    adjustment_factor = sidebar_config["adjustment_factor"]
    scenario_desc = sidebar_config["scenario_desc"]
    lead_time_days = sidebar_config["lead_time_days"]

    # Generate Forecast Button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 Generate Forecast", type="primary", use_container_width=True):
        with st.spinner("🔮 Forecasting demand..."):
            try:
                # Call FastAPI backend
                base_forecast = get_forecast(selected_category, horizon)

                if base_forecast:
                    # Apply scenario adjustments
                    adjusted_forecast = [val * adjustment_factor for val in base_forecast]

                    # Store in session state
                    st.session_state["forecast"] = adjusted_forecast
                    st.session_state["scenario"] = scenario_desc
                    st.session_state["horizon"] = horizon
                    st.session_state["product"] = product
                    st.session_state["lead_time_days"] = lead_time_days

                    st.sidebar.success("✅ Forecast generated!")
                else:
                    st.sidebar.error("❌ No forecast returned from API")

            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
                if "401" in str(e) or "Unauthorized" in str(e):
                    st.sidebar.warning("🔑 Hint: Check your FASTAPI_API_KEY in Streamlit Cloud secrets")
                elif "404" in str(e):
                    st.sidebar.warning("📍 Hint: Verify FASTAPI_URL is correct")
                elif "timeout" in str(e).lower() or "timed out" in str(e).lower():
                    st.sidebar.warning("⏱️ Hint: FastAPI may be cold-starting (wait 30-45s and retry)")
                else:
                    st.sidebar.warning("🔍 Check Streamlit Cloud logs for details")

    # Info box
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **💡 How It Works:**
    1. Select product & forecast horizon
    2. Choose a scenario (Normal, Promo, etc.)
    3. Click 'Generate Forecast'
    4. View charts, data, stock recommendations, and AI insights!
    """)

    # Add logo and credits
    st.sidebar.markdown("---")
    st.sidebar.caption("🚀 Built with Databricks + Streamlit")
    st.sidebar.caption("📊 Powered by AutoETS + MLflow")
    st.sidebar.caption("🤖 AI Insights by Groq LLaMA 3.3")

    # ========================================================================
    # MAIN CONTENT AREA (TABS)
    # ========================================================================

    if "forecast" in st.session_state and st.session_state["forecast"]:
        forecast = st.session_state["forecast"]
        scenario_desc = st.session_state["scenario"]
        horizon = st.session_state["horizon"]
        product = st.session_state["product"]
        lead_time_days = st.session_state["lead_time_days"]
    
        # Create tabs with a unique key to preserve state across reruns
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📊 Forecast Chart",
                "📋 Data Table",
                "🎯 Stock Recommendations",
                "💡 AI Insights",
            ],
            key="main_tabs"  # ✅ FIX: Preserve tab state when "Get AI Answer" button is clicked
        )
    
        with tab1:
            df_forecast = render_forecast_tab(forecast, horizon, product, scenario_desc)
    
        with tab2:
            render_data_tab(df_forecast, product)
    
        with tab3:
            render_stock_tab(forecast, lead_time_days, calculate_stock_recommendation)
    
        with tab4:
            render_insights_tab(forecast, product, scenario_desc, lead_time_days, calculate_stock_recommendation)
    
    else:
        render_welcome_screen()
    
    # Footer
    st.markdown("---")
    st.caption("🚀 InventoryForge v1.0 | Built for Impact pSiddhi S2-D-02 | Powered by Databricks + Streamlit")


if __name__ == "__main__":
    main()
