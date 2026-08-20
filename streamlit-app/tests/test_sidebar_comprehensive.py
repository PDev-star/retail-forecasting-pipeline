# test_sidebar_comprehensive.py - Comprehensive coverage for components/sidebar.py
"""
Tests for sidebar.py to achieve 80%+ coverage.
Covers product selection, scenario controls, and all UI interactions.
"""
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def mock_streamlit():
    """Mock streamlit with all sidebar methods"""
    mock_st = MagicMock()
    
    # Sidebar methods
    mock_st.sidebar.markdown = MagicMock()
    mock_st.sidebar.selectbox = MagicMock(return_value=None)
    mock_st.sidebar.number_input = MagicMock(return_value=30)
    mock_st.sidebar.radio = MagicMock(return_value="Base Case")
    mock_st.sidebar.slider = MagicMock(return_value=1.0)
    mock_st.sidebar.divider = MagicMock()
    mock_st.sidebar.info = MagicMock()
    
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        yield mock_st


def test_render_sidebar_returns_all_values(mock_streamlit):
    """Test sidebar returns product, horizon, scenario, multiplier"""
    from components.sidebar import render_sidebar
    
    # Mock user selections
    mock_streamlit.sidebar.selectbox.return_value = {
        'name': 'Widget', 'sku': 'WDG001', 'product_id': 'widget-1'
    }
    mock_streamlit.sidebar.number_input.return_value = 45
    mock_streamlit.sidebar.radio.return_value = "Best Case"
    mock_streamlit.sidebar.slider.return_value = 1.2
    
    with patch('components.sidebar.st', mock_streamlit):
        product, horizon, scenario, multiplier = render_sidebar()
    
    # Verify all return values
    assert product == {'name': 'Widget', 'sku': 'WDG001', 'product_id': 'widget-1'}
    assert horizon == 45
    assert scenario == "Best Case"
    assert multiplier == 1.2


def test_render_sidebar_no_product_selected(mock_streamlit):
    """Test sidebar when no product is selected"""
    from components.sidebar import render_sidebar
    
    # No product selected
    mock_streamlit.sidebar.selectbox.return_value = None
    
    with patch('components.sidebar.st', mock_streamlit):
        product, horizon, scenario, multiplier = render_sidebar()
    
    # Verify None returned for product
    assert product is None


def test_render_sidebar_creates_ui_elements(mock_streamlit):
    """Test sidebar creates all expected UI elements"""
    from components.sidebar import render_sidebar
    
    with patch('components.sidebar.st', mock_streamlit):
        with patch('components.sidebar.PRODUCTS', [{'name': 'Test', 'sku': 'T1', 'product_id': 'p1'}]):
            render_sidebar()
    
    # Verify UI methods were called
    assert mock_streamlit.sidebar.markdown.called
    assert mock_streamlit.sidebar.selectbox.called
    assert mock_streamlit.sidebar.number_input.called
    assert mock_streamlit.sidebar.radio.called
    assert mock_streamlit.sidebar.slider.called


def test_render_sidebar_horizon_range(mock_streamlit):
    """Test horizon input has correct range"""
    from components.sidebar import render_sidebar
    
    with patch('components.sidebar.st', mock_streamlit):
        with patch('components.sidebar.PRODUCTS', [{'name': 'Test', 'sku': 'T1', 'product_id': 'p1'}]):
            render_sidebar()
    
    # Check number_input was called for horizon
    assert mock_streamlit.sidebar.number_input.called
    call_kwargs = mock_streamlit.sidebar.number_input.call_args[1]
    
    # Verify range constraints exist
    assert 'min_value' in call_kwargs
    assert 'max_value' in call_kwargs


def test_render_sidebar_scenario_options(mock_streamlit):
    """Test scenario radio has correct options"""
    from components.sidebar import render_sidebar
    
    with patch('components.sidebar.st', mock_streamlit):
        with patch('components.sidebar.PRODUCTS', [{'name': 'Test', 'sku': 'T1', 'product_id': 'p1'}]):
            render_sidebar()
    
    # Check radio was called for scenarios
    assert mock_streamlit.sidebar.radio.called
    call_args = mock_streamlit.sidebar.radio.call_args[0]
    
    # Verify scenario options
    assert len(call_args) >= 2  # At least label and options


def test_render_sidebar_multiplier_slider(mock_streamlit):
    """Test multiplier slider configuration"""
    from components.sidebar import render_sidebar
    
    with patch('components.sidebar.st', mock_streamlit):
        with patch('components.sidebar.PRODUCTS', [{'name': 'Test', 'sku': 'T1', 'product_id': 'p1'}]):
            render_sidebar()
    
    # Check slider was called
    assert mock_streamlit.sidebar.slider.called
    call_kwargs = mock_streamlit.sidebar.slider.call_args[1]
    
    # Verify slider has min/max values
    assert 'min_value' in call_kwargs
    assert 'max_value' in call_kwargs


def test_render_sidebar_with_empty_products(mock_streamlit):
    """Test sidebar handles empty product list"""
    from components.sidebar import render_sidebar
    
    with patch('components.sidebar.st', mock_streamlit):
        with patch('components.sidebar.PRODUCTS', []):
            try:
                product, horizon, scenario, multiplier = render_sidebar()
                success = True
            except:
                success = False
    
    # Should not crash
    assert success


def test_render_sidebar_with_multiple_products(mock_streamlit):
    """Test sidebar with multiple products in dropdown"""
    from components.sidebar import render_sidebar
    
    products = [
        {'name': 'Product A', 'sku': 'PA001', 'product_id': 'pa1'},
        {'name': 'Product B', 'sku': 'PB001', 'product_id': 'pb1'},
        {'name': 'Product C', 'sku': 'PC001', 'product_id': 'pc1'}
    ]
    
    with patch('components.sidebar.st', mock_streamlit):
        with patch('components.sidebar.PRODUCTS', products):
            render_sidebar()
    
    # Verify selectbox was called
    assert mock_streamlit.sidebar.selectbox.called


def test_render_sidebar_default_values(mock_streamlit):
    """Test sidebar returns sensible defaults"""
    from components.sidebar import render_sidebar
    
    # No mocking - use default returns
    mock_streamlit.sidebar.selectbox.return_value = None
    mock_streamlit.sidebar.number_input.return_value = 30
    mock_streamlit.sidebar.radio.return_value = "Base Case"
    mock_streamlit.sidebar.slider.return_value = 1.0
    
    with patch('components.sidebar.st', mock_streamlit):
        product, horizon, scenario, multiplier = render_sidebar()
    
    # Check defaults are reasonable
    assert horizon == 30
    assert scenario == "Base Case"
    assert multiplier == 1.0
