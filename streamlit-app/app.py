# app.py - Retail Forecasting Streamlit App
# Deploy to Streamlit Community Cloud

import sys
import os
import threading

# Conditional streamlit import - tests import functions without running UI
try:
    import streamlit as st
    
    # Page configuration (only when streamlit is available)
    st.set_page_config(
        page_title="Retail Forecasting Engine",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except ImportError:
    # Test environment - create minimal mock for imports
    class MockStreamlit:
        class session_state(dict):
            pass
        session_state = session_state()
        @staticmethod
        def set_page_config(**kwargs): pass
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    st = MockStreamlit()

# ============================================================================
# CONFIGURATION AND SERVICES
# ============================================================================
from utils.config import FASTAPI_URL, API_KEY, PRODUCTS, keep_fastapi_warm
from services.api_client import get_forecast
from services.inventory import calculate_stock_recommendation

# Re-export for backward compatibility (tests import from app)
__all__ = ['get_forecast', 'calculate_stock_recommendation', 'FASTAPI_URL', 'API_KEY', 'PRODUCTS']


# ============================================================================
# SMART PYTEST GUARD
# ============================================================================
# This guard allows:
#   1. Normal Streamlit app execution (pytest not in modules)
#   2. Integration tests via AppTest (APPTEST_MODE=1)
#   3. Blocks UI for unit tests (pytest in modules, no APPTEST_MODE)

def _should_run_ui() -> bool:
    """
    Determine if UI code should execute.
    
    Returns True when:
      - APPTEST_MODE=1 (integration tests need UI)
      - OR pytest not in sys.modules (normal Streamlit app)
    
    Returns False when:
      - pytest in sys.modules AND no APPTEST_MODE (unit tests)
    """
    # Integration tests explicitly set APPTEST_MODE
    if os.environ.get('APPTEST_MODE') == '1':
        return True
    
    # Unit tests have pytest in modules but no APPTEST_MODE
    if 'pytest' in sys.modules or 'PYTEST_CURRENT_TEST' in os.environ:
        return False
    
    # Normal Streamlit app execution
    return True


# ============================================================================
# UI COMPONENTS
# ============================================================================
from components.sidebar import render_sidebar
from components.tabs import (
    render_forecast_tab,
    render_data_tab,
    render_stock_tab,
    render_insights_tab,
    render_welcome_screen,
)

# ============================================================================
# MAIN APP (Skip during unit testing, run for integration tests)
# ============================================================================

if _should_run_ui():
    # Start keep-alive thread (MOVED INSIDE UI guard to prevent test issues)
    if FASTAPI_URL != "http://localhost:8000":
        if "keep_alive_started" not in st.session_state:
            st.session_state.keep_alive_started = True
            ping_thread = threading.Thread(target=keep_fastapi_warm, daemon=True)
            ping_thread.start()
            print(f"🚀 Keep-alive thread started for {FASTAPI_URL}")
    
    # Render sidebar and get parameters
    sidebar_state = render_sidebar(PRODUCTS)
    
    product = sidebar_state["product"]
    horizon = sidebar_state["horizon"]
    adjustment_factor = sidebar_state["adjustment_factor"]
    scenario_desc = sidebar_state["scenario_desc"]
    lead_time_days = sidebar_state["lead_time_days"]
    selected_category = sidebar_state["selected_category"]
    scenario_type = sidebar_state["scenario_type"]
    
    # Main content area
    st.title(f"📈 {product['name']}")
    st.markdown(f"**SKU:** {product['sku']} | **Category:** {selected_category}")
    st.markdown("---")
    
    # Fetch forecast button
    if st.button("🔮 Generate Forecast", type="primary", use_container_width=True):
        with st.spinner(f"Fetching {horizon}-day forecast via FastAPI Gateway..."):
            forecast = get_forecast(product["product_id"], horizon)
    
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
    
    # Display results or welcome screen
    if "forecast" in st.session_state:
        forecast = st.session_state["forecast"]
        scenario_desc = st.session_state["scenario"]
        horizon = st.session_state["horizon"]
        product = st.session_state["product"]
        lead_time_days = st.session_state["lead_time_days"]
    
        # Create tabs with persistent state
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Forecast Chart",
            "📋 Data Table",
            "🎯 Stock Recommendations",
            "💡 AI Insights",
        ], key="main_tabs")
    
        with tab1:
            df_forecast = render_forecast_tab(forecast, horizon, product, scenario_desc)
    
        with tab2:
            render_data_tab(df_forecast, product)
    
        with tab3:
            render_stock_tab(forecast, lead_time_days, calculate_stock_recommendation)
    
        with tab4:
            render_insights_tab(forecast, product, scenario_desc, lead_time_days, calculate_stock_recommendation)
    
    else:
        # Show welcome screen
        render_welcome_screen()
