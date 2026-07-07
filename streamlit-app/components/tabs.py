# Tab content rendering components

from datetime import datetime
import pandas as pd
import streamlit as st
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
    """Render the AI insights tab."""
    st.markdown("### 💡 AI-Powered Insights")

    # Calculate metrics
    recommended_stock = calculate_stock_recommendation(forecast, lead_time_days)
    safety_stock = int(recommended_stock * 0.2)
    reorder_point = int(sum(forecast[:lead_time_days]))
    
    # Generate insights
    avg_demand = sum(forecast) / len(forecast)
    trend = "increasing" if forecast[-1] > forecast[0] else "decreasing"
    volatility = max(forecast) - min(forecast)

    st.markdown(f"""
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
    """)

    st.info("""
    **Note:** These insights are generated using AutoETS forecasting model with MLflow tracking. 
    Forecasts are updated daily with latest sales data. For critical business decisions, 
    consult with procurement and operations teams.
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
