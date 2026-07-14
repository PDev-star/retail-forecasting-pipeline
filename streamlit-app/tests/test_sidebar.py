# Tests for components/sidebar.py

import pytest
from unittest.mock import MagicMock, patch
from components.sidebar import render_sidebar


# Mock PRODUCTS constant
MOCK_PRODUCTS = {
    "Cat1": {
        "name": "WHITE HANGING HEART T-LIGHT HOLDER",
        "sku": "22469",
        "product_id": "Cat1",
        "color": "#FF6B6B"
    },
    "Cat2": {
        "name": "JUMBO BAG RED RETROSPOT",
        "sku": "22083",
        "product_id": "Cat2",
        "color": "#4ECDC4"
    }
}


def test_render_sidebar_returns_correct_structure():
    """Test that render_sidebar returns a dict with all required keys"""
    with patch('components.sidebar.st') as mock_st:
        # Mock sidebar methods
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",  # Product selection
            "Normal"  # Scenario type
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        # Verify all required keys present
        assert "selected_category" in result
        assert "product" in result
        assert "horizon" in result
        assert "scenario_type" in result
        assert "adjustment_factor" in result
        assert "scenario_desc" in result
        assert "lead_time_days" in result


def test_render_sidebar_normal_scenario():
    """Test Normal scenario returns correct values"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Normal"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Normal"
        assert result["adjustment_factor"] == 1.0
        assert result["scenario_desc"] == "Standard business-as-usual forecast"
        assert result["lead_time_days"] == 14


def test_render_sidebar_promotion_scenario():
    """Test Promotion scenario returns correct adjustment factor"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "JUMBO BAG RED RETROSPOT",
            "Promotion (+30%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Promotion (+30%)"
        assert result["adjustment_factor"] == 1.3
        assert result["scenario_desc"] == "30% demand increase due to promotional campaign"
        assert result["lead_time_days"] == 14


def test_render_sidebar_supply_disruption_scenario():
    """Test Supply Disruption scenario with custom lead time"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Supply Disruption"
        ])
        mock_st.sidebar.slider = MagicMock(side_effect=[30, 21])  # horizon, then lead_time
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Supply Disruption"
        assert result["adjustment_factor"] == 1.0
        assert result["scenario_desc"] == "Normal demand, but consider supply delays"
        assert result["lead_time_days"] == 21


def test_render_sidebar_seasonal_peak_scenario():
    """Test Seasonal Peak scenario returns correct adjustment factor"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "JUMBO BAG RED RETROSPOT",
            "Seasonal Peak (+50%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Seasonal Peak (+50%)"
        assert result["adjustment_factor"] == 1.5
        assert result["scenario_desc"] == "50% demand increase during seasonal peak"
        assert result["lead_time_days"] == 14


def test_render_sidebar_black_friday_scenario():
    """Test Black Friday Sale scenario returns correct adjustment factor"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Black Friday Sale (+80%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Black Friday Sale (+80%)"
        assert result["adjustment_factor"] == 1.8
        assert result["scenario_desc"] == "80% demand surge during Black Friday event"
        assert result["lead_time_days"] == 10


def test_render_sidebar_clearance_scenario():
    """Test End of Season Clearance scenario"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "JUMBO BAG RED RETROSPOT",
            "End of Season Clearance (+40%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "End of Season Clearance (+40%)"
        assert result["adjustment_factor"] == 1.4
        assert result["scenario_desc"] == "40% demand increase during clearance sale"
        assert result["lead_time_days"] == 14


def test_render_sidebar_product_launch_scenario():
    """Test Product Launch scenario"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Product Launch (+60%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Product Launch (+60%)"
        assert result["adjustment_factor"] == 1.6
        assert result["scenario_desc"] == "60% demand increase for new product launch"
        assert result["lead_time_days"] == 21


def test_render_sidebar_competitor_entry_scenario():
    """Test Competitor Entry scenario (negative adjustment)"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "JUMBO BAG RED RETROSPOT",
            "Competitor Entry (-20%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Competitor Entry (-20%)"
        assert result["adjustment_factor"] == 0.8
        assert result["scenario_desc"] == "20% demand decrease due to new competitor"
        assert result["lead_time_days"] == 14


def test_render_sidebar_economic_downturn_scenario():
    """Test Economic Downturn scenario (negative adjustment)"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Economic Downturn (-30%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Economic Downturn (-30%)"
        assert result["adjustment_factor"] == 0.7
        assert result["scenario_desc"] == "30% demand decrease during economic slowdown"
        assert result["lead_time_days"] == 21


def test_render_sidebar_holiday_season_scenario():
    """Test Holiday Season scenario"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "JUMBO BAG RED RETROSPOT",
            "Holiday Season (+70%)"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["scenario_type"] == "Holiday Season (+70%)"
        assert result["adjustment_factor"] == 1.7
        assert result["scenario_desc"] == "70% demand increase during holiday season"
        assert result["lead_time_days"] == 10


def test_render_sidebar_product_mapping():
    """Test that product display names correctly map back to product IDs"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "JUMBO BAG RED RETROSPOT",  # This should map to Cat2
            "Normal"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["selected_category"] == "Cat2"
        assert result["product"]["name"] == "JUMBO BAG RED RETROSPOT"
        assert result["product"]["sku"] == "22083"


def test_render_sidebar_custom_horizon():
    """Test that custom horizon values are returned correctly"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Normal"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=60)  # Custom horizon
        
        result = render_sidebar(MOCK_PRODUCTS)
        
        assert result["horizon"] == 60


def test_render_sidebar_displays_sku_caption():
    """Test that SKU and category caption is displayed"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Normal"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        render_sidebar(MOCK_PRODUCTS)
        
        # Verify caption was called with SKU and category info
        mock_st.sidebar.caption.assert_called_once()
        caption_call = mock_st.sidebar.caption.call_args[0][0]
        assert "SKU: 22469" in caption_call
        assert "Category: Cat1" in caption_call


def test_render_sidebar_ui_elements_called():
    """Test that all sidebar UI elements are created"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Normal"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        render_sidebar(MOCK_PRODUCTS)
        
        # Verify UI elements were called
        mock_st.sidebar.title.assert_called_once()
        assert mock_st.sidebar.markdown.call_count >= 3  # Multiple markdown calls
        mock_st.sidebar.caption.assert_called_once()
        assert mock_st.sidebar.selectbox.call_count == 2  # Product and scenario
        mock_st.sidebar.slider.assert_called()  # At least once for horizon


def test_render_sidebar_all_scenarios_have_parameters():
    """Test that all scenario types return valid parameters"""
    scenarios = [
        "Normal",
        "Promotion (+30%)",
        "Supply Disruption",
        "Seasonal Peak (+50%)",
        "Black Friday Sale (+80%)",
        "End of Season Clearance (+40%)",
        "Product Launch (+60%)",
        "Competitor Entry (-20%)",
        "Economic Downturn (-30%)",
        "Holiday Season (+70%)"
    ]
    
    for scenario in scenarios:
        with patch('components.sidebar.st') as mock_st:
            mock_st.sidebar.title = MagicMock()
            mock_st.sidebar.markdown = MagicMock()
            mock_st.sidebar.caption = MagicMock()
            
            # Supply Disruption has an extra slider call
            if scenario == "Supply Disruption":
                mock_st.sidebar.selectbox = MagicMock(side_effect=[
                    "WHITE HANGING HEART T-LIGHT HOLDER",
                    scenario
                ])
                mock_st.sidebar.slider = MagicMock(side_effect=[30, 21])
            else:
                mock_st.sidebar.selectbox = MagicMock(side_effect=[
                    "WHITE HANGING HEART T-LIGHT HOLDER",
                    scenario
                ])
                mock_st.sidebar.slider = MagicMock(return_value=30)
            
            result = render_sidebar(MOCK_PRODUCTS)
            
            # Verify all required fields are present and valid
            assert result["scenario_type"] == scenario
            assert isinstance(result["adjustment_factor"], (int, float))
            assert result["adjustment_factor"] > 0  # All factors should be positive
            assert isinstance(result["scenario_desc"], str)
            assert len(result["scenario_desc"]) > 0
            assert isinstance(result["lead_time_days"], int)
            assert result["lead_time_days"] > 0


def test_render_sidebar_scenario_options_list_length():
    """Test that scenario options list contains all expected scenarios"""
    with patch('components.sidebar.st') as mock_st:
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.caption = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(side_effect=[
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "Normal"
        ])
        mock_st.sidebar.slider = MagicMock(return_value=30)
        
        render_sidebar(MOCK_PRODUCTS)
        
        # Get the scenario selectbox call
        selectbox_calls = mock_st.sidebar.selectbox.call_args_list
        # Second call should be for scenarios
        scenario_call = selectbox_calls[1]
        scenario_options = scenario_call[0][1]  # Second positional arg is the options list
        
        # Verify we have 10 scenario options
        assert len(scenario_options) == 10
        assert "Normal" in scenario_options
        assert "Black Friday Sale (+80%)" in scenario_options
        assert "Economic Downturn (-30%)" in scenario_options
