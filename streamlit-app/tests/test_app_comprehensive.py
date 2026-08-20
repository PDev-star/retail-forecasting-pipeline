# test_app_comprehensive.py - Comprehensive coverage tests for app.py
"""
Additional tests to achieve 80%+ coverage for app.py main logic.
Tests the main application flow including product selection and tab rendering.
"""
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def mock_streamlit():
    """Mock streamlit for app tests"""
    mock_st = MagicMock()
    
    # Mock all streamlit UI components
    mock_st.set_page_config = MagicMock()
    mock_st.title = MagicMock()
    mock_st.markdown = MagicMock()
    mock_st.info = MagicMock()
    mock_st.selectbox = MagicMock(return_value="Product 1")
    mock_st.number_input = MagicMock(return_value=7)
    mock_st.selectbox = MagicMock(return_value="Base Case")
    mock_st.button = MagicMock(return_value=False)
    mock_st.tabs = MagicMock(return_value=[MagicMock() for _ in range(5)])
    mock_st.spinner = MagicMock(return_value=MagicMock(__enter__=lambda x: x, __exit__=lambda *args: None))
    mock_st.success = MagicMock()
    mock_st.error = MagicMock()
    mock_st.warning = MagicMock()
    
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        yield mock_st


def test_app_page_config(mock_streamlit):
    """Test app sets page config correctly"""
    with patch('app.st', mock_streamlit):
        with patch('app.render_sidebar'):
            with patch('app.render_welcome_screen'):
                import app
                # Force reload to trigger page config
                import importlib
                importlib.reload(app)
    
    # Verify page config was called
    assert mock_streamlit.set_page_config.called


def test_app_renders_welcome_when_no_product(mock_streamlit):
    """Test app renders welcome screen when no product selected"""
    with patch('app.st', mock_streamlit):
        with patch('app.render_sidebar', return_value=(None, 30, "Base", 1.0)):
            with patch('app.render_welcome_screen') as mock_welcome:
                import app
                import importlib
                importlib.reload(app)
                
                # Verify welcome screen was called
                assert mock_welcome.called


def test_app_fetches_forecast_on_product_select(mock_streamlit):
    """Test app fetches forecast when product is selected"""
    mock_product = {
        'name': 'Test Product',
        'sku': 'TST001',
        'product_id': 'test-product-1'
    }
    
    mock_forecast_result = {
        'dates': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'forecast': [100, 110, 120],
        'model': 'AutoETS'
    }
    
    with patch('app.st', mock_streamlit):
        with patch('app.render_sidebar', return_value=(mock_product, 30, "Base", 1.0)):
            with patch('app.get_forecast', return_value=mock_forecast_result) as mock_get_forecast:
                with patch('app.render_forecast_tab'):
                    with patch('app.render_data_tab'):
                        with patch('app.render_stock_tab'):
                            with patch('app.render_insights_tab'):
                                with patch('app.render_gemini_tab'):
                                    import app
                                    import importlib
                                    importlib.reload(app)
                                    
                                    # Verify forecast was fetched
                                    assert mock_get_forecast.called


def test_app_renders_all_tabs_on_success(mock_streamlit):
    """Test app renders all 5 tabs when forecast succeeds"""
    mock_product = {
        'name': 'Widget',
        'sku': 'WDG001',
        'product_id': 'widget-1'
    }
    
    mock_forecast_result = {
        'dates': ['2024-01-01'] * 30,
        'forecast': [100] * 30,
        'model': 'Prophet'
    }
    
    # Create tab mocks
    tab_mocks = [MagicMock() for _ in range(5)]
    for tab in tab_mocks:
        tab.__enter__ = lambda self: self
        tab.__exit__ = lambda *args: None
    
    mock_streamlit.tabs.return_value = tab_mocks
    
    with patch('app.st', mock_streamlit):
        with patch('app.render_sidebar', return_value=(mock_product, 30, "Normal", 1.0)):
            with patch('app.get_forecast', return_value=mock_forecast_result):
                with patch('app.render_forecast_tab') as mock_forecast_tab:
                    with patch('app.render_data_tab') as mock_data_tab:
                        with patch('app.render_stock_tab') as mock_stock_tab:
                            with patch('app.render_insights_tab') as mock_insights_tab:
                                with patch('app.render_gemini_tab') as mock_gemini_tab:
                                    import app
                                    import importlib
                                    importlib.reload(app)
                                    
                                    # Verify all tab render functions were called
                                    assert mock_forecast_tab.called
                                    assert mock_data_tab.called
                                    assert mock_stock_tab.called
                                    assert mock_insights_tab.called
                                    assert mock_gemini_tab.called


def test_app_handles_forecast_api_error(mock_streamlit):
    """Test app handles API errors gracefully"""
    mock_product = {
        'name': 'Test',
        'sku': 'TST',
        'product_id': 'test'
    }
    
    with patch('app.st', mock_streamlit):
        with patch('app.render_sidebar', return_value=(mock_product, 30, "Base", 1.0)):
            with patch('app.get_forecast', side_effect=Exception("API Error")):
                import app
                import importlib
                
                # Should not crash
                try:
                    importlib.reload(app)
                    success = True
                except:
                    success = False
                
                assert success  # App should handle errors gracefully
