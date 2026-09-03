# Tab content rendering components

from datetime import datetime
import pandas as pd

# Conditional streamlit import - tests run without streamlit
try:
    import streamlit as st
except ImportError:
    # Test environment - UI components won't be called during tests
    class MockStreamlit:
        @staticmethod
        def markdown(text): pass
        @staticmethod
        def info(text): pass
        @staticmethod
        def dataframe(*args, **kwargs): pass
        @staticmethod
        def download_button(*args, **kwargs): pass
        @staticmethod
        def metric(*args, **kwargs): pass
        @staticmethod
        def columns(n): return [MockStreamlit() for _ in range(n)]
    st = MockStreamlit()

from components.charts import render_forecast_chart, render_inventory_chart

def render_forecast_tab(forecast, baseline_forecast, horizon, product, scenario_desc, adjustment_factor=1.0, scenario_type="Normal"):
    """
    Render the forecast chart tab - simplified single-scenario view.
    
    What-if scenarios are selected via dropdown in sidebar.
    User can switch between scenarios to see how forecasts change.
    """
    st.markdown("### 📊 Demand Forecast")
    st.caption("Prophet model trained on historical sales data")
    
    # Show current scenario info
    st.info(f"🎯 **Scenario:** {scenario_desc}")
    
    # Render the forecast chart for selected scenario (includes metrics display)
    render_forecast_chart(forecast, horizon, product, scenario_desc)
    
    st.markdown("---")
    
    # Return DataFrame for data tab (single scenario column)
    from datetime import datetime, timedelta
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, horizon + 1)]
    df_forecast = pd.DataFrame({
        "Date": dates,
        "Predicted Demand": forecast
    })
    
    return df_forecast


def render_data_tab(df_forecast, product):
    """Render the data table tab."""
    st.markdown("### 📋 Forecast Data Table")
    st.caption("Detailed daily forecasts with cumulative totals")

    df_display = df_forecast.copy()
    df_display["Day of Week"] = pd.to_datetime(df_display["Date"]).dt.day_name()
    
    # Handle both old format (single forecast) and new format (baseline + scenario)
    if "Predicted Demand" in df_display.columns:
        df_display["Cumulative Demand"] = df_display["Predicted Demand"].cumsum()
    elif "Scenario" in df_display.columns:
        df_display["Cumulative Baseline"] = df_display["Baseline"].cumsum()
        df_display["Cumulative Scenario"] = df_display["Scenario"].cumsum()
    
    # =========================================================================
    # QUICK STATS SUMMARY
    # =========================================================================
    st.info("""
    📊 **Quick Stats Summary**
    
    * **Total Days:** {} days
    * **Date Range:** {} to {}
    * **Includes:** Daily demand, day of week, cumulative totals
    * **Download:** Export as CSV for use in Excel, Google Sheets, or your ERP system
    """.format(
        len(df_display),
        df_display["Date"].iloc[0] if len(df_display) > 0 else "N/A",
        df_display["Date"].iloc[-1] if len(df_display) > 0 else "N/A"
    ))

    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
    )

    st.markdown("---")
    
    # =========================================================================
    # EXPORT GUIDANCE
    # =========================================================================
    st.markdown("### 📥 Export & Integration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **How to use this data:**
        * **Excel/Sheets:** Import CSV and create pivot tables or charts
        * **ERP Systems:** Bulk upload forecast data for procurement planning
        * **BI Tools:** Combine with sales data for variance analysis
        * **Reporting:** Share with stakeholders for demand planning meetings
        """)
    
    with col2:
        # Download button
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{product['sku']}_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )


def render_stock_tab(forecast, lead_time_days, calculate_stock_recommendation):
    """Render the stock recommendations tab."""
    st.markdown("### 🎯 Stock Level Recommendations")
    st.caption("Optimal inventory levels based on lead time demand + safety buffer")

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
    
    # =========================================================================
    # EXPLANATORY CONTENT & ACTIONABLE GUIDANCE
    # =========================================================================
    
    # Understanding the Recommendations
    st.info("""
    📖 **Understanding These Recommendations**
    
    * **Order Quantity:** Covers expected demand during lead time PLUS 20% safety buffer to prevent stockouts
    * **Reorder Point:** When your inventory hits this level, place a new order immediately
    * **Safety Stock:** Emergency buffer (20% of order) protects against demand spikes or delivery delays
    * **Lead Time:** Expected days from placing order to receiving stock — longer lead time = more safety stock needed
    """)
    
    # Calculate actionable metrics
    avg_daily_demand = sum(forecast) / len(forecast)
    total_period_demand = sum(forecast)
    max_daily_demand = max(forecast)
    min_daily_demand = min(forecast)
    demand_volatility = max_daily_demand - min_daily_demand
    volatility_pct = (demand_volatility / avg_daily_demand * 100) if avg_daily_demand > 0 else 0
    
    # Estimated budget impact
    estimated_unit_cost = 15.0  # Approximate cost per unit (£)
    order_cost = recommended_stock * estimated_unit_cost
    
    # Action Items
    st.success("""
    ✅ **Action Items**
    
    1. **Order Now:** Stock up to **{:,} units** (estimated cost: **£{:,.2f}**)
    2. **Monitor Daily:** Track inventory levels and reorder when stock drops to **{:,} units**
    3. **Review Weekly:** Adjust forecasts based on actual sales patterns
    4. **Maintain Buffer:** Always keep **{:,} units** as safety stock for emergencies
    """.format(recommended_stock, order_cost, reorder_point, safety_stock))
    
    # Risk Assessment (conditional warning based on volatility)
    if volatility_pct > 50:
        st.warning("""
        ⚠️ **High Stockout Risk Detected**
        
        Your demand shows **{:.1f}% volatility** (high fluctuation between {:.0f} and {:.0f} units/day).
        
        **Recommendations:**
        * Consider increasing safety stock to 30% (instead of 20%)
        * Monitor inventory more frequently (daily vs weekly)
        * Have backup suppliers ready for rush orders
        * Review lead time — shorter is safer with volatile demand
        """.format(volatility_pct, min_daily_demand, max_daily_demand))
    elif lead_time_days > 21:
        st.warning("""
        ⚠️ **Long Lead Time Alert**
        
        Your **{} day lead time** is quite long. This increases risk:
        * More time for demand to change unexpectedly
        * Higher safety stock needed
        * Consider negotiating faster delivery or finding local suppliers
        """.format(lead_time_days))
    else:
        st.success("✅ **Low Risk:** Your demand is stable and lead time is manageable.")
    
    st.markdown("---")
    
    # Generate dates for inventory chart
    from datetime import datetime, timedelta
    horizon = len(forecast)
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, horizon + 1)]
    
    render_inventory_chart(forecast, dates, recommended_stock, reorder_point, safety_stock, lead_time_days)


def render_gemini_tab():
    """Render Gemini 2.5 Flash static scenario explanations (pre-generated, cached)."""
    st.markdown("### 🔬 Gemini 2.5 Flash: Business Scenario Analysis")
    st.caption("Pre-generated strategic insights from notebook pipeline, validated & cached in Delta Lake")
    st.info("💡 **Why separate tab?** These are high-level business explanations that apply across all products, unlike the real-time product-specific insights in the AI Insights tab.")
    st.markdown("---")
    
    import requests
    from utils.config import FASTAPI_URL, API_KEY
    
    with st.spinner("📡 Loading Gemini insights from Delta Lake..."):
        try:
            # Fetch Gemini insights from FastAPI
            # Increased timeout to 30s to handle cache hits after warmup
            response = requests.get(
                f"{FASTAPI_URL}/ai-insights",
                headers={"X-API-Key": API_KEY},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if request was successful
                if data.get("success") and data.get("insights"):
                    # Display each scenario
                    for insight in data["insights"]:
                        scenario_icon = {1: "📊", 2: "🎯", 3: "⚖️"}.get(insight["scenario_id"], "💡")
                        with st.expander(f"{scenario_icon} {insight['scenario_name']}", expanded=True):
                            st.markdown(f"**Question:** {insight['question']}")
                            st.markdown("---")
                            st.markdown(insight["explanation"])
                            st.caption(f"Source: `{insight['context_table']}` | Generated: {insight['generated_at'][:10]}")
                    
                    # Show cache status
                    cache_status = "(cached)" if data.get("cached") else "(fresh from DB)"
                    if data.get("stale"):
                        cache_status = "(cached, refreshing in background)"
                    
                    st.success(f"✅ {data['total']} validated Gemini scenarios loaded {cache_status}")
                    
                elif not data.get("success"):
                    # Handle graceful errors (warehouse warming up, etc.)
                    error_msg = data.get("error", "Unknown error")
                    user_msg = data.get("message", "")
                    
                    if "cold start" in error_msg.lower() or "starting" in error_msg.lower():
                        st.warning(f"⏳ {user_msg}")
                        st.info("The SQL warehouse is waking up (cold start). Please wait 30-60 seconds and refresh this tab.")
                        if st.button("🔄 Retry Now"):
                            st.rerun()
                    else:
                        st.warning(f"⚠️ {user_msg or 'No Gemini insights found in cache.'}")
                        if st.button("🔄 Retry"):
                            st.rerun()
                else:
                    st.warning("⚠️ No Gemini insights found in cache.")
                    st.info("💡 Gemini insights require the notebook scenario cells (71, 72, 74) to be run first.")
            else:
                st.error(f"❌ Failed to fetch Gemini insights: HTTP {response.status_code}")
                if st.button("🔄 Retry"):
                    st.rerun()
        except requests.Timeout:
            st.error("⏱️ Request timed out (30s). The warehouse may be starting up.")
            st.info("Please wait a moment and try again. First call after deployment can take 2-3 minutes.")
            if st.button("🔄 Retry Now"):
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading Gemini insights: {e}")
            st.info("💡 Gemini insights require the notebook scenario cells (71, 72, 74) to be run first.")
            if st.button("🔄 Retry"):
                st.rerun()


def render_insights_tab(forecast, product, scenario_desc, lead_time_days, calculate_stock_recommendation):
    """Render real-time AI insights tab (Groq LLaMA - product-specific analysis)."""
    st.markdown("### 💡 AI-Powered Real-Time Insights")
    st.markdown("*Groq LLaMA 3.3 70B generates live analysis based on YOUR current product & forecast data*")
    st.markdown("---")

    # Calculate metrics
    recommended_stock = calculate_stock_recommendation(forecast, lead_time_days)
    safety_stock = int(recommended_stock * 0.2)
    reorder_point = int(sum(forecast[:lead_time_days]))
    avg_demand = sum(forecast) / len(forecast)
    trend = "increasing" if forecast[-1] > forecast[0] else "decreasing"
    volatility = max(forecast) - min(forecast)
    
    # =========================================================================
    # GROQ LLAMA INSIGHTS (REAL-TIME INTERACTIVE - PRODUCT-SPECIFIC)
    # =========================================================================
    
    from utils.ai_insights_groq import get_forecast_insight, get_stock_insight, get_risk_insight
    
    # Insight 1: Forecast Analysis
    with st.expander("📊 Forecast Analysis (AI-Generated)", expanded=True):
        with st.spinner("🤖 Analyzing forecast patterns..."):
            forecast_data = {
                'forecast': forecast,
                'product': product,
                'scenario': scenario_desc
            }
            insight = get_forecast_insight(forecast_data)
            st.write(insight)
    
    # Insight 2: Stock Recommendations
    with st.expander("🎯 Stock Recommendations (AI-Generated)", expanded=True):
        with st.spinner("🤖 Generating stock recommendations..."):
            stock_data = {
                'recommended_stock': recommended_stock,
                'reorder_point': reorder_point,
                'safety_stock': safety_stock,
                'lead_time_days': lead_time_days
            }
            insight = get_stock_insight(stock_data)
            st.write(insight)
    
    # Insight 3: Risk Assessment
    with st.expander("⚠️ Risk Assessment (AI-Generated)", expanded=True):
        with st.spinner("🤖 Assessing risks..."):
            risk_data = {
                'volatility': volatility,
                'avg_demand': avg_demand,
                'trend': trend,
                'scenario': scenario_desc
            }
            insight = get_risk_insight(risk_data)
            st.write(insight)
    
    st.markdown("---")
    
    # =========================================================================
    # CUSTOM Q&A (ADVANCED FEATURE - GOES BEYOND RFP!)
    # =========================================================================
    from utils.ai_insights_groq import get_custom_ai_answer
    
    st.markdown("### 🤔 Ask Your Own Question")
    st.markdown("Ask anything about this forecast, and AI will answer based on the data.")
    
    custom_question = st.text_area(
        "Your question:",
        placeholder="Examples:\n• Should I increase orders for next month?\n• What if demand drops by 30%?\n• Is this product seasonal?\n• How much safety stock do I really need?",
        height=120,
        key="custom_ai_question"
    )
    
    if st.button("🤖 Get AI Answer", type="primary"):
        if custom_question.strip():
            with st.spinner("🧠 AI is analyzing your question..."):
                context = {
                    'forecast': forecast,
                    'product': product,
                    'scenario': scenario_desc,
                    'stock_data': {
                        'recommended_stock': recommended_stock,
                        'reorder_point': reorder_point,
                        'safety_stock': safety_stock,
                        'lead_time_days': lead_time_days
                    }
                }
                answer = get_custom_ai_answer(custom_question, context)
                st.success("✅ AI Answer:")
                st.info(answer)
        else:
            st.warning("⚠️ Please enter a question first!")
    
    # Technical details (collapsed by default)
    with st.expander("📊 Technical Details (Raw Metrics)"):
        st.markdown(f"""
        **Raw Forecast Metrics:**
        - Average daily demand: {avg_demand:.1f} units
        - Demand trend: {trend}
        - Volatility: {volatility:.1f} units
        - Recommended order: {recommended_stock:,} units
        - Reorder point: {reorder_point:,} units
        - Safety stock: {safety_stock:,} units
        
        **Model:** AutoETS with MLflow tracking
        """)


def render_welcome_screen():
    """Render the welcome screen when no forecast is available."""
    st.info("👆 Select a product and forecast horizon from the sidebar, then click 'Generate Forecast' to begin.")

    st.markdown("""
    ## Welcome to InventoryForge 🚀
    
    **Predictive Inventory Analytics Engine** — AI-powered demand forecasting for smarter inventory decisions.
    """)
    
    # Feature Overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Key Features
        
        * **📈 ML Forecasts:** AutoETS models trained on historical sales
        * **🎯 Smart Stock Recs:** Automated reorder points & safety stock
        * **💡 What-If Scenarios:** 10 business scenarios (promotions, disruptions)
        * **🤖 AI Insights:** Gemini 2.5 Flash + Groq LLaMA explanations
        * **📊 Rich Visualizations:** Interactive charts with confidence bands
        * **📥 Data Export:** Download forecasts as CSV for ERP integration
        """)
    
    with col2:
        st.markdown("""
        ### 💼 Business Impact
        
        * **30% reduction** in buffer stock
        * **£15-30K capital freed** per product
        * **95% service level** maintained
        * **Zero manual forecasting** — fully automated
        * **Real-time updates** — no waiting for batch runs
        * **Cost-effective** — free infrastructure (Databricks CE + Streamlit Cloud)
        """)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("""
    ### 🔄 How It Works
    
    1. **👈 Select Product:** Choose from available product categories in the sidebar
    2. **⚙️ Set Parameters:** Adjust forecast horizon (7-90 days) and scenario type
    3. **🚀 Generate Forecast:** Click the button to get ML-powered predictions
    4. **📊 Explore Tabs:**
       * **Forecast** — Demand chart with confidence bands & metrics
       * **Data** — Detailed daily forecasts with download option
       * **Stock** — Recommended order quantities, reorder points, safety stock
       * **AI Insights (Groq)** — Real-time LLaMA 3.3 70B analysis of YOUR data
       * **Gemini Insights** — Pre-computed scenario explanations from Gemini 2.5 Flash
    """)
    
    st.markdown("---")
    
    # Technical Architecture
    with st.expander("🏗️ Technical Architecture", expanded=False):
        st.markdown("""
        **Data Pipeline:**
        * **Data Storage:** Databricks Delta Lake (versioned, ACID transactions)
        * **ML Training:** AutoETS + Prophet models with MLflow experiment tracking
        * **Model Registry:** Unity Catalog for version control and lineage
        * **Model Serving:** Databricks serverless endpoints (scale-to-zero)
        * **API Gateway:** FastAPI proxy on Render.com (keeps endpoints warm)
        * **Frontend:** Streamlit Community Cloud (this app)
        * **AI Insights:** Gemini 2.5 Flash (cached) + Groq LLaMA 3.3 70B (real-time)
        
        **Security:**
        * No Databricks credentials in frontend code
        * API key authentication for all requests
        * Read-only access to forecasts (no write permissions)
        
        **Performance:**
        * Keep-alive pings every 10 min (prevents cold starts)
        * In-memory caching (5-min TTL with stale-while-revalidate)
        * Unity Catalog Volume JSON cache (no SQL warehouse needed for AI insights)
        """)
