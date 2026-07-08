# test_ui_integration.py - Comprehensive Integration Tests
"""
Full integration test suite for Streamlit UI using AppTest.
Tests complete user workflows, state management, and UI rendering.

Requires APPTEST_MODE=1 to enable UI during pytest.
Coverage target: 80%+ for RFP S2-D-02 compliance.
"""
import os
import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch, MagicMock


# ============================================================================
# PYTEST FIXTURE: Enable APPTEST_MODE for all integration tests
# ============================================================================
@pytest.fixture(autouse=True)
def enable_apptest_mode():
    """
    Enable UI for integration tests by setting APPTEST_MODE=1.
    This allows app.py's smart guard to run UI code during pytest.
    """
    os.environ['APPTEST_MODE'] = '1'
    yield
    os.environ.pop('APPTEST_MODE', None)


# ============================================================================
# TEST 1: App Initialization
# ============================================================================
def test_app_loads_successfully():
    """Test: App loads without errors and renders initial UI"""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    
    # Verify no errors on load
    assert len(at.exception) == 0, "App should load without exceptions"
    
    # Verify key UI elements exist
    assert len(at.button) > 0, "Forecast button should exist"
    assert "forecast" not in at.session_state, "Should start without forecast"


# ============================================================================
# TEST 2: Successful Forecast Generation
# ============================================================================
def test_successful_forecast_generation_workflow():
    """Test: User generates forecast → API called → Results displayed"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Mock successful API response
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test Product"},
            "forecast": {
                "horizon_days": 14,
                "values": [45.2, 43.8, 44.1, 46.0, 45.5, 44.8, 45.3,
                          46.2, 45.9, 46.5, 47.0, 46.8, 47.2, 47.5]
            },
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        # Find and click forecast button
        forecast_button = [btn for btn in at.button 
                          if "Generate Forecast" in str(btn)][0]
        forecast_button.click().run()
        
        # Verify API was called
        assert mock_post.called, "API should be called"
        
        # Verify forecast stored in session
        assert "forecast" in at.session_state, "Forecast should be stored"
        assert len(at.session_state["forecast"]) == 14
        
        # Verify success message displayed
        assert len(at.success) > 0, "Success message should display"


# ============================================================================
# TEST 3: Product Selection (Cat2)
# ============================================================================
def test_product_selection_cat2():
    """Test: Selecting different product category (Cat2)"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find product selector and switch to Cat2
    for selectbox in at.selectbox:
        if "Select Product" in str(selectbox.label):
            # Get the Cat2 option
            options = selectbox.options
            cat2_option = [opt for opt in options if "Cat2" in opt][0]
            selectbox.set_value(cat2_option).run()
            break
    
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
    
    with patch('services.api_client.requests.post') as mock_post:
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Cannot connect to server"
        )
        
        # Click forecast button
        at.button[0].click().run()
        
        # Verify error message displayed
        assert len(at.error) > 0, "Error message should display"
        error_text = at.error[0].value
        assert "Cannot connect" in error_text
        
        # Verify no forecast stored
        assert "forecast" not in at.session_state


# ============================================================================
# TEST 5: API 401 Unauthorized Error
# ============================================================================
def test_api_unauthorized_error_handling():
    """Test: Invalid API key → User sees 401 error"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify error handling
        assert len(at.error) > 0
        assert "forecast" not in at.session_state


# ============================================================================
# TEST 6: API 500 Server Error
# ============================================================================
def test_api_server_error_handling():
    """Test: Server error → User sees appropriate message"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        assert len(at.error) > 0
        assert "forecast" not in at.session_state


# ============================================================================
# TEST 7: Empty Forecast Values Handling
# ============================================================================
def test_empty_forecast_values_handled_gracefully():
    """Test: API returns empty forecast → No session state stored"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1", "name": "Test"},
            "forecast": {"horizon_days": 14, "values": []},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Empty forecast should not be stored (empty list evaluates to False)
        assert "forecast" not in at.session_state


# ============================================================================
# TEST 8: Promotion Scenario (+30%)
# ============================================================================
def test_promotion_scenario_applies_correctly():
    """Test: Promotion scenario applies 1.3x adjustment factor"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find and select "Promotion (+30%)" scenario (adjustment_factor = 1.3)
    for selectbox in at.selectbox:
        if "Scenario" in str(selectbox.label):
            selectbox.set_value("Promotion (+30%)").run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1"},
            "forecast": {"horizon_days": 3, "values": [10.0, 20.0, 30.0]},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify adjustment applied: [10, 20, 30] * 1.3 = [13, 26, 39]
        forecast = at.session_state["forecast"]
        assert forecast[0] == 13.0
        assert forecast[1] == 26.0
        assert forecast[2] == 39.0


# ============================================================================
# TEST 9: Supply Disruption Scenario
# ============================================================================
def test_supply_disruption_scenario():
    """Test: Supply Disruption scenario with custom lead time"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find and select "Supply Disruption" scenario
    for selectbox in at.selectbox:
        if "Scenario" in str(selectbox.label):
            selectbox.set_value("Supply Disruption").run()
            break
    
    # This should enable a lead time slider - adjust it
    for slider in at.slider:
        if "Lead Time" in str(slider.label):
            slider.set_value(21).run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1"},
            "forecast": {"horizon_days": 3, "values": [10.0, 20.0, 30.0]},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Supply Disruption has adjustment_factor = 1.0 (no change)
        forecast = at.session_state["forecast"]
        assert forecast[0] == 10.0
        assert forecast[1] == 20.0
        assert forecast[2] == 30.0
        
        # Verify lead time was stored
        assert at.session_state["lead_time_days"] == 21


# ============================================================================
# TEST 10: Seasonal Peak Scenario (+50%)
# ============================================================================
def test_seasonal_peak_scenario():
    """Test: Seasonal Peak scenario applies 1.5x adjustment factor"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find and select "Seasonal Peak (+50%)" scenario
    for selectbox in at.selectbox:
        if "Scenario" in str(selectbox.label):
            selectbox.set_value("Seasonal Peak (+50%)").run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1"},
            "forecast": {"horizon_days": 3, "values": [10.0, 20.0, 30.0]},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify adjustment applied: [10, 20, 30] * 1.5 = [15, 30, 45]
        forecast = at.session_state["forecast"]
        assert forecast[0] == 15.0
        assert forecast[1] == 30.0
        assert forecast[2] == 45.0


# ============================================================================
# TEST 11: Horizon Parameter Changes
# ============================================================================
def test_different_horizon_values():
    """Test: Changing horizon parameter requests different forecast lengths"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Find horizon slider and change to 21
    for slider in at.slider:
        if "Horizon" in str(slider.label):
            slider.set_value(21).run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1"},
            "forecast": {"horizon_days": 21, "values": [10.0] * 21},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify API called with horizon=21
        call_args = mock_post.call_args
        assert call_args[1]["params"]["horizon"] == 21
        
        # Verify 21 values stored
        assert len(at.session_state["forecast"]) == 21


# ============================================================================
# TEST 12: Multiple Forecast Generations (State Persistence)
# ============================================================================
def test_multiple_forecast_generations_update_state():
    """Test: Generating forecast twice updates state correctly"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        # First forecast
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1"},
            "forecast": {"horizon_days": 3, "values": [10.0, 20.0, 30.0]},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        first_forecast = at.session_state["forecast"].copy()
        assert first_forecast == [10.0, 20.0, 30.0]
        
        # Second forecast with different values
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1"},
            "forecast": {"horizon_days": 3, "values": [40.0, 50.0, 60.0]},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        
        at.button[0].click().run()
        second_forecast = at.session_state["forecast"]
        
        # Verify state updated to new forecast
        assert second_forecast == [40.0, 50.0, 60.0]
        assert second_forecast != first_forecast


# ============================================================================
# TEST 13: Malformed API Response Handling
# ============================================================================
def test_malformed_api_response_handled_gracefully():
    """Test: Invalid response structure → Error shown, no crash"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            # Missing 'forecast' key entirely
            "product": {"id": "Cat1"}
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Should handle gracefully with error message
        assert len(at.error) > 0
        assert "forecast" not in at.session_state


# ============================================================================
# TEST 14: JSON Decode Error Handling
# ============================================================================
def test_json_decode_error_handled():
    """Test: Invalid JSON response → Error displayed"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        assert len(at.error) > 0
        assert "forecast" not in at.session_state


# ============================================================================
# TEST 15: Timeout Error Handling
# ============================================================================
def test_api_timeout_handled():
    """Test: Request timeout → Error message shown"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    with patch('services.api_client.requests.post') as mock_post:
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        at.button[0].click().run()
        
        assert len(at.error) > 0
        assert "forecast" not in at.session_state


# ============================================================================
# TEST 16: Long Forecast (90 days)
# ============================================================================
def test_long_forecast_90_days():
    """Test: Maximum horizon (90 days) forecast generation"""
    at = AppTest.from_file("../app.py")
    at.run()
    
    # Set horizon to maximum
    for slider in at.slider:
        if "Horizon" in str(slider.label):
            slider.set_value(90).run()
            break
    
    with patch('services.api_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "product": {"id": "Cat1"},
            "forecast": {"horizon_days": 90, "values": [25.0] * 90},
            "generated_at": "2026-07-03T10:30:00Z"
        }
        mock_post.return_value = mock_response
        
        at.button[0].click().run()
        
        # Verify 90-day forecast stored
        assert len(at.session_state["forecast"]) == 90
