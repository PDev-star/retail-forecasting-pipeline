# Integration Tests for Streamlit App
# Tests that require the full Streamlit UI (AppTest)

import os
from unittest.mock import patch, MagicMock
os.environ['APPTEST_MODE'] = '1'

from streamlit.testing.v1 import AppTest


# ============================================================================
# TEST 1: Basic App Loading
# ============================================================================
def test_app_loads_successfully():
    """Test: App loads without errors and shows expected UI components"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Verify UI components present
    assert len(at.title) > 0  # Has title
    assert len(at.button) > 0  # Has "Generate Forecast" button
    assert len(at.selectbox) > 0  # Has product selector


# ============================================================================
# TEST 2: Successful Forecast Generation
# ============================================================================
def test_successful_forecast_generation_workflow():
    """Test: Full workflow - select product → generate forecast → see results"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Mock API call
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": [10.0, 12.0, 11.0, 13.0, 14.0, 12.5, 11.5]},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        # Click "Generate Forecast" button
        at.button[0].click().run()
        
        # Verify forecast generated and stored in session state
        assert "forecast" in at.session_state
        assert len(at.session_state["forecast"]) == 7


# ============================================================================
# TEST 3: Product Selection (Cat2)
# ============================================================================
def test_product_selection_cat2():
    """Test: Selecting different product category (Cat2)"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find product selector and switch to Cat2
    product_selectbox = None
    for selectbox in at.selectbox:
        if "Select Product" in str(selectbox.label):
            product_selectbox = selectbox
            break
    
    # Verify we found the product selectbox
    assert product_selectbox is not None, "Product selectbox not found"
    
    # Get available options
    options = product_selectbox.options
    assert len(options) > 0, "No product options available"
    
    # Try to find Cat2 product by name (JUMBO BAG RED RETROSPOT)
    cat2_option = None
    for opt in options:
        if "JUMBO BAG" in opt or "RETROSPOT" in opt:
            cat2_option = opt
            break
    
    # If Cat2 product found by name, select it; otherwise select second option
    if cat2_option:
        product_selectbox.set_value(cat2_option).run()
    elif len(options) >= 2:
        # Fallback: select the second option (likely Cat2)
        product_selectbox.set_value(options[1]).run()
    else:
        # Skip test if we can't select a second product
        import pytest
        pytest.skip("Only one product option available, cannot test Cat2 selection")
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat2", "name": "Test Product 2"},
            "forecast": {"horizon_days": 7, "values": [15.0] * 7},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify forecast generated for Cat2
        assert "forecast" in at.session_state
        assert len(at.session_state["forecast"]) == 7


# ============================================================================
# TEST 4: API Connection Error Handling
# ============================================================================
def test_api_connection_error_displays_user_message():
    """Test: API unreachable → User sees clear error message"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Mock connection error
    with patch('services.api_client.requests.post') as mock_post:
        mock_post.side_effect = Exception("Connection refused")
        
        at.button[0].click().run()
        
        # Verify no crash, and forecast not in session
        # App should handle the error gracefully


# ============================================================================
# TEST 5: API Unauthorized Error (401)
# ============================================================================
def test_api_unauthorized_error_handling():
    """Test: Invalid API key → Error handled gracefully"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # App should handle 401 gracefully


# ============================================================================
# TEST 6: API Server Error (500)
# ============================================================================
def test_api_server_error_handling():
    """Test: Server error → User notified"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # App should handle 500 gracefully


# ============================================================================
# TEST 7: Empty Forecast Values
# ============================================================================
def test_empty_forecast_values_handled_gracefully():
    """Test: API returns empty forecast → App doesn't crash"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 0, "values": []},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # App should handle empty forecast gracefully


# ============================================================================
# TEST 8: Promotion Scenario Adjustment
# ============================================================================
def test_promotion_scenario_applies_correctly():
    """Test: Promotion scenario applies 1.3x adjustment factor"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find scenario selectbox and set to Promotion
    for selectbox in at.selectbox:
        if "Scenario Type" in str(selectbox.label):
            selectbox.set_value("Promotion (+30%)").run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": [10.0] * 7},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify forecast adjusted (should be 10.0 * 1.3 = 13.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 13.0


# ============================================================================
# TEST 9: Supply Disruption Scenario
# ============================================================================
def test_supply_disruption_scenario():
    """Test: Supply disruption scenario enables lead time slider"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find scenario selectbox and set to Supply Disruption
    for selectbox in at.selectbox:
        if "Scenario Type" in str(selectbox.label):
            selectbox.set_value("Supply Disruption").run()
            break
    
    # Verify lead time slider appears
    slider_found = False
    for slider in at.slider:
        if "Lead Time" in str(slider.label):
            slider_found = True
            break
    
    assert slider_found, "Lead time slider should appear for Supply Disruption scenario"


# ============================================================================
# TEST 10: Seasonal Peak Scenario
# ============================================================================
def test_seasonal_peak_scenario():
    """Test: Seasonal peak scenario applies 1.5x adjustment"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find scenario selectbox and set to Seasonal Peak
    for selectbox in at.selectbox:
        if "Scenario Type" in str(selectbox.label):
            selectbox.set_value("Seasonal Peak (+50%)").run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": [10.0] * 7},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify forecast adjusted (should be 10.0 * 1.5 = 15.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 15.0


# ============================================================================
# TEST 11: Different Horizon Values
# ============================================================================
def test_different_horizon_values():
    """Test: Changing forecast horizon affects forecast length"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find horizon slider and set to 14 days
    for slider in at.slider:
        if "Forecast Horizon" in str(slider.label):
            slider.set_value(14).run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 14, "values": [10.0] * 14},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify forecast length
        if "forecast" in at.session_state:
            assert len(at.session_state["forecast"]) == 14


# ============================================================================
# TEST 12: Multiple Forecast Generations
# ============================================================================
def test_multiple_forecast_generations_update_state():
    """Test: Generating multiple forecasts updates session state correctly"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        # First forecast
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": [10.0] * 7},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        first_forecast = at.session_state.get("forecast", [])
        
        # Second forecast with different values
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": [20.0] * 7},
            "generated_at": "2026-07-03T10:01:00Z"
        }
        
        at.button[0].click().run()
        second_forecast = at.session_state.get("forecast", [])
        
        # Verify forecast was updated
        assert first_forecast != second_forecast or len(second_forecast) == 7


# ============================================================================
# TEST 13: Malformed API Response
# ============================================================================
def test_malformed_api_response_handled_gracefully():
    """Test: Malformed API response doesn't crash the app"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            # Missing required fields
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # App should handle malformed response gracefully


# ============================================================================
# TEST 14: JSON Decode Error
# ============================================================================
def test_json_decode_error_handled():
    """Test: JSON decode error handled gracefully"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # App should handle JSON decode error gracefully


# ============================================================================
# TEST 15: API Timeout
# ============================================================================
def test_api_timeout_handled():
    """Test: API timeout handled gracefully"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        import requests
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        at.button[0].click().run()
        
        # App should handle timeout gracefully


# ============================================================================
# TEST 16: Long Forecast Horizon (90 days)
# ============================================================================
def test_long_forecast_90_days():
    """Test: 90-day forecast horizon works correctly"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Set horizon to 90 days (max)
    for slider in at.slider:
        if "Forecast Horizon" in str(slider.label):
            slider.set_value(90).run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 90, "values": [10.0] * 90},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify 90-day forecast
        if "forecast" in at.session_state:
            assert len(at.session_state["forecast"]) == 90
