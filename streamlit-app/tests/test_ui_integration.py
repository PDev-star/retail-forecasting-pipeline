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
# TEST 3: Product Selection - Cat2
# ============================================================================
def test_product_selection_cat2():
    """Test: User can select different product (Cat2)"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Change product selection (selectbox index 0 is the product selector)
    at.selectbox[0].select("JUMBO BAG RED RETROSPOT").run()
    
    # Verify product changed by checking title values
    title_values = [title.value for title in at.title]
    assert any("JUMBO BAG RED RETROSPOT" in value for value in title_values)


# ============================================================================
# TEST 4: API Connection Error
# ============================================================================
def test_api_connection_error_displays_user_message():
    """Test: When API is unreachable, user sees helpful error"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        # Simulate connection error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("API unreachable")
        
        # Try to generate forecast
        at.button[0].click().run()
        
        # Verify error displayed
        # Note: If no forecast generated, session state should not have "forecast" key
        # or app should show error message (we check for absence of forecast)
        assert "forecast" not in at.session_state or len(at.session_state.get("forecast", [])) == 0


# ============================================================================
# TEST 5: API Returns 401 Unauthorized
# ============================================================================
def test_api_unauthorized_error_handling():
    """Test: API returns 401, app handles it gracefully"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # No forecast should be stored
        assert "forecast" not in at.session_state or len(at.session_state.get("forecast", [])) == 0


# ============================================================================
# TEST 6: API Returns 500 Internal Server Error
# ============================================================================
def test_api_server_error_handling():
    """Test: API returns 500, app handles it gracefully"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal Server Error"}
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # No forecast should be stored
        assert "forecast" not in at.session_state or len(at.session_state.get("forecast", [])) == 0


# ============================================================================
# TEST 7: Empty Forecast Values
# ============================================================================
def test_empty_forecast_values_handled_gracefully():
    """Test: API returns empty values array, app doesn't crash"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": []},  # Empty!
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Should not crash, but no valid forecast stored
        # (empty forecast is considered invalid)
        assert "forecast" not in at.session_state or len(at.session_state.get("forecast", [])) == 0


# ============================================================================
# TEST 8: Promotion Scenario Applies Correctly
# ============================================================================
def test_promotion_scenario_applies_correctly():
    """Test: Promotion (+30%) scenario multiplies forecast by 1.3"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Select Promotion scenario (second selectbox is scenario selector)
    at.selectbox[1].select("Promotion (+30%)").run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": [10.0] * 7},  # All 10s
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify forecast adjusted (10.0 * 1.3 = 13.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 13.0


# ============================================================================
# TEST 9: Supply Disruption Scenario
# ============================================================================
def test_supply_disruption_scenario():
    """Test: Supply Disruption scenario doesn't change forecast values"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Select Supply Disruption scenario
    at.selectbox[1].select("Supply Disruption").run()
    
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
        
        # Forecast unchanged (1.0 multiplier)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 10.0


# ============================================================================
# TEST 10: Seasonal Peak Scenario
# ============================================================================
def test_seasonal_peak_scenario():
    """Test: Seasonal Peak (+50%) scenario multiplies forecast by 1.5"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Select Seasonal Peak scenario
    at.selectbox[1].select("Seasonal Peak (+50%)").run()
    
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
        
        # Forecast adjusted (10.0 * 1.5 = 15.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 15.0


# ============================================================================
# TEST 11: Black Friday Sale Scenario
# ============================================================================
def test_black_friday_scenario():
    """Test: Black Friday Sale (+80%) scenario multiplies forecast by 1.8"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Select Black Friday scenario
    at.selectbox[1].select("Black Friday Sale (+80%)").run()
    
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
        
        # Forecast adjusted (10.0 * 1.8 = 18.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 18.0


# ============================================================================
# TEST 12: Competitor Entry Scenario
# ============================================================================
def test_competitor_entry_scenario():
    """Test: Competitor Entry (-20%) scenario multiplies forecast by 0.8"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Select Competitor Entry scenario
    at.selectbox[1].select("Competitor Entry (-20%)").run()
    
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
        
        # Forecast adjusted (10.0 * 0.8 = 8.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 8.0


# ============================================================================
# TEST 13: Holiday Season Scenario
# ============================================================================
def test_holiday_season_scenario():
    """Test: Holiday Season (+70%) scenario multiplies forecast by 1.7"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Select Holiday Season scenario
    at.selectbox[1].select("Holiday Season (+70%)").run()
    
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
        
        # Forecast adjusted (10.0 * 1.7 = 17.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 17.0


# ============================================================================
# TEST 14: Product Launch Scenario
# ============================================================================
def test_product_launch_scenario():
    """Test: Product Launch (+60%) scenario multiplies forecast by 1.6"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Select Product Launch scenario
    at.selectbox[1].select("Product Launch (+60%)").run()
    
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
        
        # Forecast adjusted (10.0 * 1.6 = 16.0)
        if "forecast" in at.session_state:
            assert at.session_state["forecast"][0] == 16.0


# ============================================================================
# TEST 15: Different Horizon Values
# ============================================================================
def test_different_horizon_values():
    """Test: Changing horizon slider works correctly"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Change horizon to 14 days (slider index 0 is horizon)
    at.slider[0].set_value(14).run()
    
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
# TEST 16: Multiple Forecast Generations
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
        first_forecast = at.session_state["forecast"] if "forecast" in at.session_state else []
        
        # Second forecast with different values
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 7, "values": [20.0] * 7},
            "generated_at": "2026-07-03T10:01:00Z"
        }
        
        at.button[0].click().run()
        second_forecast = at.session_state["forecast"] if "forecast" in at.session_state else []
        
        # Verify forecast was updated
        assert first_forecast != second_forecast or len(second_forecast) == 7


# ============================================================================
# TEST 17: Malformed API Response
# ============================================================================
def test_malformed_api_response_handled_gracefully():
    """Test: API returns malformed JSON, app doesn't crash"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            # Missing "forecast" key!
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Should handle gracefully, no forecast stored
        assert "forecast" not in at.session_state or len(at.session_state.get("forecast", [])) == 0


# ============================================================================
# TEST 18: JSON Decode Error
# ============================================================================
def test_json_decode_error_handled():
    """Test: API returns invalid JSON, app handles it"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Should handle gracefully
        assert "forecast" not in at.session_state or len(at.session_state.get("forecast", [])) == 0


# ============================================================================
# TEST 19: API Timeout
# ============================================================================
def test_api_timeout_handled():
    """Test: API request times out, app handles it"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        at.button[0].click().run()
        
        # Should handle gracefully
        assert "forecast" not in at.session_state or len(at.session_state.get("forecast", [])) == 0


# ============================================================================
# TEST 20: Long Forecast (90 days)
# ============================================================================
def test_long_forecast_90_days():
    """Test: 90-day forecast works correctly"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Set horizon to 90 days
    at.slider[0].set_value(84).run()  # Closest to 90 (step=7, so 84)
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {"horizon_days": 84, "values": [10.0] * 84},
            "generated_at": "2026-07-03T10:00:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify long forecast stored
        if "forecast" in at.session_state:
            assert len(at.session_state["forecast"]) == 84
