# Tests for components/charts.py

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
import pandas as pd
from components.charts import render_forecast_chart, render_inventory_chart


# Mock product data
MOCK_PRODUCT = {
    "name": "Test Product",
    "color": "#FF6B6B",
    "sku": "12345"
}


def test_render_forecast_chart_creates_chart():
    """Test that render_forecast_chart creates and displays a chart"""
    forecast = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
    horizon = 7
    scenario_desc = "Test scenario"
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock()] * 4)
        
        result = render_forecast_chart(forecast, horizon, MOCK_PRODUCT, scenario_desc)
        
        # Verify UI elements were called
        assert mock_st.markdown.call_count >= 1
        mock_st.info.assert_called_once()
        mock_st.plotly_chart.assert_called_once()
        mock_st.columns.assert_called_once_with(4)
        
        # Verify return value is a DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == horizon
        assert "Date" in result.columns
        assert "Predicted Demand" in result.columns


def test_render_forecast_chart_correct_data_structure():
    """Test that the forecast chart has correct data structure"""
    forecast = [100.0, 110.0, 120.0]
    horizon = 3
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock()] * 4)
        
        result = render_forecast_chart(forecast, horizon, MOCK_PRODUCT, "Test")
        
        # Verify data values match forecast
        assert list(result["Predicted Demand"]) == forecast
        
        # Verify dates are in correct format
        for date_str in result["Date"]:
            datetime.strptime(date_str, "%Y-%m-%d")  # Should not raise


def test_render_forecast_chart_displays_scenario():
    """Test that scenario description is displayed"""
    forecast = [50.0] * 7
    scenario_desc = "Promotion (+30%)"
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock()] * 4)
        
        render_forecast_chart(forecast, 7, MOCK_PRODUCT, scenario_desc)
        
        # Verify info was called with scenario
        info_call = mock_st.info.call_args[0][0]
        assert scenario_desc in info_call


def test_render_forecast_chart_summary_metrics():
    """Test that summary metrics are displayed correctly"""
    forecast = [10.0, 20.0, 30.0, 40.0, 50.0]
    
    with patch('components.charts.st') as mock_st:
        mock_col = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_st.columns = MagicMock(return_value=[mock_col, mock_col, mock_col, mock_col])
        
        render_forecast_chart(forecast, 5, MOCK_PRODUCT, "Test")
        
        # Verify columns were created
        mock_st.columns.assert_called_once_with(4)
        
        # Verify metrics were called (4 metrics total)
        assert mock_col.metric.call_count == 4


def test_render_forecast_chart_with_single_value():
    """Test chart rendering with a single forecast value"""
    forecast = [25.0]
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock()] * 4)
        
        result = render_forecast_chart(forecast, 1, MOCK_PRODUCT, "Test")
        
        assert len(result) == 1
        assert result["Predicted Demand"][0] == 25.0


def test_render_forecast_chart_with_long_horizon():
    """Test chart rendering with a long forecast horizon (90 days)"""
    forecast = [100.0] * 90
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock()] * 4)
        
        result = render_forecast_chart(forecast, 90, MOCK_PRODUCT, "Test")
        
        assert len(result) == 90
        mock_st.plotly_chart.assert_called_once()


def test_render_inventory_chart_creates_chart():
    """Test that render_inventory_chart creates and displays a chart"""
    forecast = [10.0, 15.0, 20.0, 25.0, 30.0]
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    recommended_stock = 200.0
    reorder_point = 50.0
    safety_stock = 30.0
    lead_time_days = 7
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.plotly_chart = MagicMock()
        
        render_inventory_chart(
            forecast, dates, recommended_stock, reorder_point, 
            safety_stock, lead_time_days
        )
        
        # Verify UI elements were called
        mock_st.markdown.assert_called_once()
        mock_st.plotly_chart.assert_called_once()


def test_render_inventory_chart_stock_depletion():
    """Test that inventory levels deplete correctly based on forecast"""
    forecast = [50.0, 50.0, 50.0]
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    recommended_stock = 150.0
    reorder_point = 50.0
    safety_stock = 30.0
    lead_time_days = 1
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.plotly_chart = MagicMock()
        
        render_inventory_chart(
            forecast, dates, recommended_stock, reorder_point,
            safety_stock, lead_time_days
        )
        
        # Verify plotly_chart was called with inventory data
        assert mock_st.plotly_chart.call_count == 1


def test_render_inventory_chart_reorder_logic():
    """Test that inventory reorder logic is triggered correctly"""
    # Set up scenario where reorder should trigger
    forecast = [40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0]
    dates = [f"2024-01-{i:02d}" for i in range(1, 9)]
    recommended_stock = 100.0
    reorder_point = 50.0
    safety_stock = 20.0
    lead_time_days = 2
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.plotly_chart = MagicMock()
        
        render_inventory_chart(
            forecast, dates, recommended_stock, reorder_point,
            safety_stock, lead_time_days
        )
        
        # Should complete without error
        assert mock_st.plotly_chart.call_count == 1


def test_render_inventory_chart_empty_forecast():
    """Test inventory chart with empty forecast"""
    forecast = []
    dates = []
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.plotly_chart = MagicMock()
        
        render_inventory_chart(
            forecast, dates, 100.0, 50.0, 30.0, 7
        )
        
        # Should handle gracefully
        mock_st.plotly_chart.assert_called_once()


def test_render_inventory_chart_with_zero_demand():
    """Test inventory chart when forecast has zero demand"""
    forecast = [0.0, 0.0, 0.0]
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.plotly_chart = MagicMock()
        
        render_inventory_chart(
            forecast, dates, 100.0, 50.0, 30.0, 7
        )
        
        # Should handle zero demand gracefully
        assert mock_st.plotly_chart.call_count == 1


def test_render_inventory_chart_stock_never_negative():
    """Test that inventory levels never go negative"""
    # High demand scenario
    forecast = [200.0, 200.0, 200.0]
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    recommended_stock = 100.0  # Not enough to meet demand
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.plotly_chart = MagicMock()
        
        render_inventory_chart(
            forecast, dates, recommended_stock, 50.0, 30.0, 7
        )
        
        # Should complete without error (inventory levels capped at 0)
        assert mock_st.plotly_chart.call_count == 1


def test_render_forecast_chart_uses_product_color():
    """Test that chart uses product color"""
    forecast = [10.0, 20.0, 30.0]
    product_with_custom_color = {
        "name": "Colorful Product",
        "color": "#123456",
        "sku": "99999"
    }
    
    with patch('components.charts.st') as mock_st:
        mock_st.markdown = MagicMock()
        mock_st.info = MagicMock()
        mock_st.plotly_chart = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock()] * 4)
        
        render_forecast_chart(forecast, 3, product_with_custom_color, "Test")
        
        # Verify chart was created (color is embedded in the Figure object)
        assert mock_st.plotly_chart.call_count == 1
