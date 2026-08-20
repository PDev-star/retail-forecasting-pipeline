"""
Comprehensive tests for components/sidebar.py
Covers all sidebar functionality: product selection, horizon, scenarios, multipliers
"""

import pytest
from unittest.mock import MagicMock, patch
from components.sidebar import render_sidebar


@pytest.fixture
def mock_products():
    """Sample PRODUCTS dict matching the app's structure"""
    return {
        "Cat1": {
            "name": "Test Product 1",
            "sku": "SKU001",
            "product_id": "Cat1",
            "color": "#1f77b4"
        },
        "Cat2": {
            "name": "Test Product 2",
            "sku": "SKU002",
            "product_id": "Cat2",
            "color": "#ff7f0e"
        }
    }


@pytest.fixture
def mock_streamlit():
    """Mock streamlit sidebar with default return values"""
    mock_sidebar = MagicMock()
    mock_sidebar.title = MagicMock()
    mock_sidebar.markdown = MagicMock()
    mock_sidebar.caption = MagicMock()
    mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 1", "Normal"])
    mock_sidebar.slider = MagicMock(return_value=30)
    
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar = mock_sidebar
        yield mock_st


def test_render_sidebar_returns_dict(mock_streamlit, mock_products):
    """Test that render_sidebar returns a dict with expected keys"""
    result = render_sidebar(mock_products)
    
    assert isinstance(result, dict)
    assert "selected_category" in result
    assert "product" in result
    assert "horizon" in result
    assert "scenario_type" in result
    assert "adjustment_factor" in result
    assert "scenario_desc" in result
    assert "lead_time_days" in result


def test_render_sidebar_normal_scenario(mock_streamlit, mock_products):
    """Test Normal scenario returns correct values"""
    result = render_sidebar(mock_products)
    
    assert result["scenario_type"] == "Normal"
    assert result["adjustment_factor"] == 1.0
    assert "business-as-usual" in result["scenario_desc"]
    assert result["lead_time_days"] == 14


def test_render_sidebar_promotion_scenario(mock_products):
    """Test Promotion scenario returns +30% adjustment"""
    mock_sidebar = MagicMock()
    mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 1", "Promotion (+30%)"])
    mock_sidebar.slider = MagicMock(return_value=30)
    
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar = mock_sidebar
        result = render_sidebar(mock_products)
    
    assert result["scenario_type"] == "Promotion (+30%)"
    assert result["adjustment_factor"] == 1.3
    assert "30%" in result["scenario_desc"]


def test_render_sidebar_black_friday_scenario(mock_products):
    """Test Black Friday scenario returns +80% adjustment"""
    mock_sidebar = MagicMock()
    mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 1", "Black Friday Sale (+80%)"])
    mock_sidebar.slider = MagicMock(return_value=30)
    
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar = mock_sidebar
        result = render_sidebar(mock_products)
    
    assert result["scenario_type"] == "Black Friday Sale (+80%)"
    assert result["adjustment_factor"] == 1.8
    assert "80%" in result["scenario_desc"]


def test_render_sidebar_competitor_scenario(mock_products):
    """Test Competitor Entry scenario returns -20% adjustment"""
    mock_sidebar = MagicMock()
    mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 1", "Competitor Entry (-20%)"])
    mock_sidebar.slider = MagicMock(return_value=30)
    
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar = mock_sidebar
        result = render_sidebar(mock_products)
    
    assert result["scenario_type"] == "Competitor Entry (-20%)"
    assert result["adjustment_factor"] == 0.8
    assert "20%" in result["scenario_desc"]


def test_render_sidebar_horizon_values(mock_products):
    """Test horizon slider returns correct values"""
    mock_sidebar = MagicMock()
    mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 1", "Normal"])
    mock_sidebar.slider = MagicMock(return_value=60)
    
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar = mock_sidebar
        result = render_sidebar(mock_products)
    
    assert result["horizon"] == 60


def test_render_sidebar_product_selection(mock_products):
    """Test product selection returns correct product"""
    mock_sidebar = MagicMock()
    mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 2", "Normal"])
    mock_sidebar.slider = MagicMock(return_value=30)
    
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar = mock_sidebar
        result = render_sidebar(mock_products)
    
    assert result["selected_category"] == "Cat2"
    assert result["product"]["name"] == "Test Product 2"
    assert result["product"]["sku"] == "SKU002"


def test_render_sidebar_creates_ui_elements(mock_streamlit, mock_products):
    """Test that UI elements are created"""
    result = render_sidebar(mock_products)
    
    # Verify sidebar methods were called
    assert mock_streamlit.sidebar.title.called
    assert mock_streamlit.sidebar.markdown.called
    assert mock_streamlit.sidebar.selectbox.called
    assert mock_streamlit.sidebar.slider.called


def test_render_sidebar_supply_disruption_slider(mock_products):
    """Test Supply Disruption scenario with custom lead time slider"""
    mock_sidebar = MagicMock()
    mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 1", "Supply Disruption"])
    mock_sidebar.slider = MagicMock(side_effect=[30, 21])  # horizon, then lead_time
    
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar = mock_sidebar
        result = render_sidebar(mock_products)
    
    assert result["scenario_type"] == "Supply Disruption"
    assert result["adjustment_factor"] == 1.0
    assert result["lead_time_days"] == 21


def test_render_sidebar_seasonal_scenarios(mock_products):
    """Test all seasonal scenarios have correct adjustments"""
    scenarios = [
        ("Seasonal Peak (+50%)", 1.5),
        ("Holiday Season (+70%)", 1.7),
        ("End of Season Clearance (+40%)", 1.4),
    ]
    
    for scenario_name, expected_factor in scenarios:
        mock_sidebar = MagicMock()
        mock_sidebar.selectbox = MagicMock(side_effect=["Test Product 1", scenario_name])
        mock_sidebar.slider = MagicMock(return_value=30)
        
        with patch('components.sidebar.st') as mock_st:
            mock_st.sidebar = mock_sidebar
            result = render_sidebar(mock_products)
        
        assert result["adjustment_factor"] == expected_factor


