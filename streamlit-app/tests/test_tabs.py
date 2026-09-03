"""
Smoke tests for components/tabs.py
"""

import pytest
from unittest.mock import MagicMock, patch


def test_all_tabs_import():
    """Test that all tab functions can be imported"""
    from components.tabs import (
        render_forecast_tab,
        render_data_tab,
        render_stock_tab,
        render_insights_tab,
        render_gemini_tab,
        render_welcome_screen,
    )
    
    assert callable(render_forecast_tab)
    assert callable(render_data_tab)
    assert callable(render_stock_tab)
    assert callable(render_insights_tab)
    assert callable(render_gemini_tab)
    assert callable(render_welcome_screen)


def test_render_gemini_tab_signature():
    """Test render_gemini_tab function signature"""
    from components.tabs import render_gemini_tab
    import inspect
    
    sig = inspect.signature(render_gemini_tab)
    # Should have no required parameters
    assert len(sig.parameters) == 0


def test_render_gemini_tab_loads_without_crash():
    """Test that render_gemini_tab doesn't crash with mocked streamlit"""
    from components.tabs import render_gemini_tab
    
    with patch('components.tabs.st'):
        # Patch requests.get at the correct location (inside the function)
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": False, "insights": []}
            mock_get.return_value = mock_response
            
            # Should not raise
            render_gemini_tab()


def test_render_forecast_tab_new_signature():
    """Test render_forecast_tab with simplified single-scenario view"""
    from components.tabs import render_forecast_tab
    
    # Create mock column objects that support context manager protocol
    mock_col1, mock_col2, mock_col3, mock_col4 = MagicMock(), MagicMock(), MagicMock(), MagicMock()
    for col in [mock_col1, mock_col2, mock_col3, mock_col4]:
        col.__enter__ = MagicMock(return_value=col)
        col.__exit__ = MagicMock(return_value=False)
        # Mock the metric and markdown methods
        col.metric = MagicMock()
        col.markdown = MagicMock()
    
    # Patch streamlit and set up mocks
    with patch('components.tabs.st') as mock_st:
        # Configure columns to return our mocked columns
        mock_st.columns = MagicMock(return_value=[mock_col1, mock_col2, mock_col3, mock_col4])
        # Mock other st methods
        mock_st.subheader = MagicMock()
        mock_st.markdown = MagicMock()
        
        with patch('components.tabs.render_forecast_chart') as mock_chart:
            with patch('components.tabs.pd') as mock_pd:
                # Mock pandas DataFrame
                mock_df = MagicMock()
                mock_df.columns = ["Predicted Demand"]
                mock_pd.DataFrame.return_value = mock_df
                
                forecast = [100.0] * 30
                baseline_forecast = [90.0] * 30
                horizon = 30
                product = {"name": "Test", "sku": "TEST001", "product_id": "cat1", "color": "#1f77b4"}
                
                # Test with Normal scenario - should render single clean view
                df_result = render_forecast_tab(
                    forecast=forecast,
                    baseline_forecast=baseline_forecast,
                    horizon=horizon,
                    product=product,
                    scenario_desc="Normal scenario",
                    adjustment_factor=1.0,
                    scenario_type="Normal"
                )
                
                # Verify chart was rendered (metrics are now in the chart, not in the tab)
                assert mock_chart.called
                # Should return the mocked DataFrame
                assert df_result is not None
                assert df_result == mock_df
