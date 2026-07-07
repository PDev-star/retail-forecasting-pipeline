# Chart rendering components

from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def render_forecast_chart(forecast, horizon, product, scenario_desc):
    """Render the demand forecast chart with confidence bands."""
    st.markdown(f"### Demand Forecast - Next {horizon} Days")
    st.info(f"**Scenario:** {scenario_desc}")

    # Prepare data for chart
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, horizon + 1)]
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
    
    return df_forecast  # Return for use in other tabs


def render_inventory_chart(forecast, dates, recommended_stock, reorder_point, safety_stock, lead_time_days):
    """Render the inventory timeline chart."""
    st.markdown("#### Inventory Timeline")

    # Inventory timeline calculation
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
