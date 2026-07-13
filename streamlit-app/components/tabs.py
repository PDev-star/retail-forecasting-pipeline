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

def render_forecast_tab(forecast, horizon, product, scenario_desc):
    """Render the forecast chart tab."""
    return render_forecast_chart(forecast, horizon, product, scenario_desc)


def render_data_tab(df_forecast, product):
    """Render the data table tab."""
    st.markdown("### Forecast Data Table")

    df_display = df_forecast.copy()
    df_display["Day of Week"] = pd.to_datetime(df_display["Date"]).dt.day_name()
    df_display["Cumulative Demand"] = df_display["Predicted Demand"].cumsum()

    st.dataframe(
        df_display.style.format({"Predicted Demand": "{:.1f}", "Cumulative Demand": "{:.0f}"}),
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


def render_stock_tab(forecast, lead_time_days, calculate_stock_recommendation):
    """Render the stock recommendations tab."""
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
    
    # Generate dates for inventory chart
    from datetime import datetime, timedelta
    horizon = len(forecast)
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, horizon + 1)]
    
    render_inventory_chart(forecast, dates, recommended_stock, reorder_point, safety_stock, lead_time_days)


def render_insights_tab(forecast, product, scenario_desc, lead_time_days, calculate_stock_recommendation):
    """Render the AI insights tab with REAL Gemini AI."""
    st.markdown("### 💡 AI-Powered Insights")
    st.markdown("*Powered by Gemini 2.5 Flash - Real AI explanations in plain English*")
    st.markdown("---")

    # Calculate metrics
    recommended_stock = calculate_stock_recommendation(forecast, lead_time_days)
    safety_stock = int(recommended_stock * 0.2)
    reorder_point = int(sum(forecast[:lead_time_days]))
    avg_demand = sum(forecast) / len(forecast)
    trend = "increasing" if forecast[-1] > forecast[0] else "decreasing"
    volatility = max(forecast) - min(forecast)
    
    # =========================================================================
    # PRE-BUILT AI INSIGHTS (3 SCENARIOS - RFP REQUIREMENT)
    # =========================================================================
    from utils.ai_insights import get_forecast_insight, get_stock_insight, get_risk_insight
    
    # Insight 1: Forecast Analysis
    with st.expander("📊 Forecast Analysis (AI-Generated)", expanded=True):
        forecast_data = {
            'forecast': forecast,
            'product': product,
            'scenario': scenario_desc
        }
        insight = get_forecast_insight(forecast_data)
        st.write(insight)
    
    # Insight 2: Stock Recommendations
    with st.expander("🎯 Stock Recommendations (AI-Generated)", expanded=True):
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
    from utils.ai_insights import get_custom_ai_answer
    
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
    - **API Gateway:** FastAPI proxy (keeps warm via 10-min pings)
    - **This App:** Streamlit (calls FastAPI gateway via REST API)
    
    **Secure & Scalable:** No Databricks credentials in frontend. All access via API key.
    """)
