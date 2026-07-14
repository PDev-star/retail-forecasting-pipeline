"""
Retail Demand Forecasting Dashboard
Streamlit app for visualizing and analyzing demand forecasts
"""

import os
# Check if running in AppTest environment
is_apptest = os.environ.get('APPTEST_MODE') == '1'

if not is_apptest:
    import streamlit as st
    from components.sidebar import render_sidebar
    from components.charts import render_forecast_chart, render_inventory_chart
    from components.tabs import render_forecast_tab, render_data_tab, render_stock_tab, render_insights_tab
    from services.inventory import calculate_stock_recommendation
    from services.api_client import get_forecast
    from utils.config import PRODUCTS, keep_fastapi_warm
    import threading
    import time
    
    # Initialize session state
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "📊 Forecast Chart"

def _should_run_ui():
    """Guard to prevent UI rendering during imports or AppTest setup."""
    return not is_apptest

def render_welcome_screen():
    """Display welcome screen when no forecast is generated."""
    if not _should_run_ui():
        return
        
    st.markdown("""
    ## 👋 Welcome to the Retail Demand Forecasting Dashboard!
    
    Get started by:
    1. **Select a product** from the sidebar
    2. **Choose a scenario** (Normal, Promotion, Supply Disruption, etc.)
    3. **Adjust the forecast horizon** (7-90 days)
    4. Click **"Generate Forecast"** to see predictions
    
    ### 🎯 What You'll Get:
    - 📊 **Interactive forecast charts** with trend analysis
    - 📋 **Detailed data tables** with downloadable CSV
    - 🎯 **Stock recommendations** based on demand and lead times
    - 💡 **AI-powered insights** to help you make better decisions
    """)
    
    st.info("💡 **Tip:** Try different scenarios to see how promotions, supply disruptions, or seasonal peaks affect demand!")

def main():
    """Main app function."""
    if not _should_run_ui():
        return
    
    # Custom CSS for smooth tab transitions
    st.markdown("""
        <style>
        /* Smooth fade-in animation for tab content */
        .main .block-container {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Style radio buttons to look more like tabs */
        div[role="radiogroup"] {
            gap: 0.5rem;
            padding: 0.5rem 0;
        }
        
        div[role="radiogroup"] label {
            background-color: transparent;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        div[role="radiogroup"] label:hover {
            background-color: rgba(255, 75, 75, 0.1);
        }
        
        div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
            display: none; /* Hide radio circles */
        }
        
        /* Highlight selected tab */
        div[role="radiogroup"] label:has(input:checked) {
            background-color: rgba(255, 75, 75, 0.15);
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🏪 Retail Demand Forecasting Dashboard")
    st.markdown("Predict future demand and optimize inventory management")
    
    # Sidebar configuration
    config = render_sidebar(PRODUCTS)
    selected_category = config["selected_category"]
    product = config["product"]
    horizon = config["horizon"]
    scenario_type = config["scenario_type"]
    adjustment_factor = config["adjustment_factor"]
    scenario_desc = config["scenario_desc"]
    lead_time_days = config["lead_time_days"]
    
    # Generate forecast button
    if st.button("🚀 Generate Forecast", type="primary", use_container_width=True):
        with st.spinner("🔮 Generating forecast..."):
            result = get_forecast(selected_category, horizon)
            
            if result and result.get("success"):
                # Extract and adjust forecast
                raw_forecast = result["forecast"]["values"]
                forecast = [v * adjustment_factor for v in raw_forecast]
                
                # Store in session state
                st.session_state["forecast"] = forecast
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
    
        # Tab navigation using radio (with fixed state management)
        tab_options = ["📊 Forecast Chart", "📋 Data Table", "🎯 Stock Recommendations", "💡 AI Insights"]
        
        # Get current tab index (default to 0 if not found)
        try:
            current_index = tab_options.index(st.session_state.active_tab)
        except (ValueError, AttributeError):
            current_index = 0
            st.session_state.active_tab = tab_options[0]
        
        # Render radio buttons with proper state
        selected_tab = st.radio(
            "Navigation",
            tab_options,
            index=current_index,
            horizontal=True,
            label_visibility="collapsed",
            key="tab_selector"  # Stable key to prevent re-initialization
        )
        
        # Update session state ONLY if tab changed
        if selected_tab != st.session_state.active_tab:
            st.session_state.active_tab = selected_tab
            st.rerun()  # Force immediate rerun for smooth transition
        
        st.markdown("---")
        
        # Render selected tab (wrapped in a container for smooth transitions)
        tab_container = st.container()
        
        with tab_container:
            if st.session_state.active_tab == "📊 Forecast Chart":
                df_forecast = render_forecast_tab(forecast, horizon, product, scenario_desc)
            
            elif st.session_state.active_tab == "📋 Data Table":
                # Generate df_forecast if not already available
                import pandas as pd
                from datetime import datetime, timedelta
                dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, horizon + 1)]
                df_forecast = pd.DataFrame({
                    "Date": dates,
                    "Predicted Demand": forecast
                })
                render_data_tab(df_forecast, product)
            
            elif st.session_state.active_tab == "🎯 Stock Recommendations":
                render_stock_tab(forecast, lead_time_days, calculate_stock_recommendation)
            
            elif st.session_state.active_tab == "💡 AI Insights":
                render_insights_tab(forecast, product, scenario_desc, lead_time_days, calculate_stock_recommendation)
    
    else:
        # Show welcome screen
        render_welcome_screen()

if __name__ == "__main__" and _should_run_ui():
    # Start keep-alive thread for API warmth (only in non-test environments)
    if not is_apptest:
        from utils.config import FASTAPI_BASE_URL
        keep_alive_thread = threading.Thread(
            target=keep_fastapi_warm,
            args=(FASTAPI_BASE_URL,),
            daemon=True
        )
        keep_alive_thread.start()
    
    main()
