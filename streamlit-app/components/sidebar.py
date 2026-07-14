# Sidebar UI component for product selection and parameters

# Conditional streamlit import - tests run without streamlit
try:
    import streamlit as st
except ImportError:
    # Test environment - UI components won't be called during tests
    # Create a minimal mock to avoid import errors
    class MockSidebar:
        @staticmethod
        def title(text): pass
        @staticmethod
        def markdown(text): pass
        @staticmethod
        def caption(text): pass
        @staticmethod
        def selectbox(*args, **kwargs):
            # Return first option if options provided
            if 'options' in kwargs:
                return kwargs['options'][0]
            return "Cat1"  # Default
        @staticmethod
        def slider(*args, **kwargs):
            # Return default value if provided, otherwise 30
            if 'value' in kwargs:
                return kwargs['value']
            return 30
    
    class MockStreamlit:
        sidebar = MockSidebar()
    
    st = MockStreamlit()

def render_sidebar(PRODUCTS):
    """
    Render the sidebar with product selection and forecast parameters.
    
    Returns:
        dict: Contains selected_category, product, horizon, scenario details
    """
    st.sidebar.title("📊 Retail Forecasting Engine")
    st.sidebar.markdown("---")
    
    # Create clean display name -> product_id mapping (product name only)
    product_display_map = {
        PRODUCTS[product_id]['name']: product_id
        for product_id in PRODUCTS.keys()
    }
    
    # Show only product name in dropdown
    selected_product_name = st.sidebar.selectbox(
        "Select Product",
        options=list(product_display_map.keys()),
        key="product_category",
    )
    
    # Map back to product_id
    selected_category = product_display_map[selected_product_name]
    product = PRODUCTS[selected_category]
    
    # Display SKU as caption below selectbox
    st.sidebar.caption(f"SKU: {product['sku']} • Category: {selected_category}")
    
    # Forecast Horizon
    st.sidebar.markdown("### Forecast Parameters")
    horizon = st.sidebar.slider("Forecast Horizon (days)", min_value=7, max_value=90, value=30, step=7)
    
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
    
    return {
        "selected_category": selected_category,
        "product": product,
        "horizon": horizon,
        "scenario_type": scenario_type,
        "adjustment_factor": adjustment_factor,
        "scenario_desc": scenario_desc,
        "lead_time_days": lead_time_days,
    }
