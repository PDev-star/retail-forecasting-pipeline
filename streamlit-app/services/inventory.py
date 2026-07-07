# Inventory and stock recommendation logic

def calculate_stock_recommendation(forecast, lead_time_days=14, safety_factor=1.2):
    """
    Calculate recommended stock levels based on forecast.

    This runs in Streamlit (NOT in Databricks) - just Python calculations!
    
    Args:
        forecast: List of forecasted demand values
        lead_time_days: Number of days of lead time (default: 14)
        safety_factor: Safety stock multiplier (default: 1.2 = 20% buffer)
    
    Returns:
        int: Recommended stock quantity
    """
    lead_time_demand = sum(forecast[:lead_time_days])
    recommended_stock = int(lead_time_demand * safety_factor)
    return recommended_stock
