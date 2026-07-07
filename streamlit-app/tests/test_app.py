# test_app.py - Unit tests for Streamlit App (FastAPI Proxy Architecture)
import os
import sys
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock streamlit before importing app
mock_st = MagicMock()
# FIXED: Mock st.secrets.get() to return actual string values
mock_st.secrets.get.side_effect = lambda key, default=None: {
    "fastapi_url": "http://localhost:8000",
    "api_key": "test-api-key-from-mock"
}.get(key, default)
sys.modules["streamlit"] = mock_st

# Import functions from app


def test_calculate_stock_recommendation():
    """Test stock recommendation calculation"""
    from app import calculate_stock_recommendation

    forecast = [10, 12, 11, 13, 10, 12, 11, 13, 10, 12, 11, 13, 10, 12]

    # Test with default parameters
    result = calculate_stock_recommendation(forecast, lead_time_days=14, safety_factor=1.2)

    expected_lead_time_demand = sum(forecast[:14])  # 160
    expected_recommended = int(expected_lead_time_demand * 1.2)  # 192

    assert result == expected_recommended


def test_calculate_stock_recommendation_custom_lead_time():
    """Test stock recommendation with custom lead time"""
    from app import calculate_stock_recommendation

    forecast = [10] * 30  # 30 days of 10 units/day

    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=1.5)

    expected_lead_time_demand = 10 * 7  # 70
    expected_recommended = int(70 * 1.5)  # 105

    assert result == expected_recommended


def test_calculate_stock_recommendation_edge_cases():
    """Test stock recommendation with edge cases"""
    from app import calculate_stock_recommendation

    # Test with forecast shorter than lead time
    short_forecast = [10, 12, 11]
    result = calculate_stock_recommendation(short_forecast, lead_time_days=7, safety_factor=1.2)
    # Should use all available data
    expected = int(sum(short_forecast) * 1.2)
    assert result == expected

    # Test with empty forecast
    empty_forecast = []
    result = calculate_stock_recommendation(empty_forecast, lead_time_days=7, safety_factor=1.2)
    assert result == 0

    # Test with zero values
    zero_forecast = [0, 0, 0, 0, 0]
    result = calculate_stock_recommendation(zero_forecast, lead_time_days=5, safety_factor=1.2)
    assert result == 0

    # Test with single value
    single_forecast = [100]
    result = calculate_stock_recommendation(single_forecast, lead_time_days=1, safety_factor=1.5)
    assert result == 150


def test_calculate_stock_recommendation_different_safety_factors():
    """Test stock recommendation with different safety factors"""
    from app import calculate_stock_recommendation

    forecast = [50, 55, 45, 60, 50, 55, 45]

    # Test with no safety stock (factor = 1.0)
    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=1.0)
    assert result == sum(forecast)

    # Test with high safety factor
    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=2.0)
    assert result == sum(forecast) * 2

    # Test with low safety factor
    result = calculate_stock_recommendation(forecast, lead_time_days=7, safety_factor=0.8)
    assert result == int(sum(forecast) * 0.8)


@patch("app.requests.post")
def test_get_forecast_success(mock_post):
    """Test successful forecast API call via FastAPI gateway"""
    from app import get_forecast

    # Mock FastAPI response format (NEW!)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "product": {"id": "Cat1", "name": "WHITE HANGING HEART T-LIGHT HOLDER"},
        "forecast": {"horizon_days": 14, "values": [45.2, 43.8, 44.1]},
        "generated_at": "2026-07-03T10:30:00Z",
    }
    mock_post.return_value = mock_response

    # Secrets already mocked at module level
    result = get_forecast("Cat1", 14)

    # Verify result
    assert result is not None
    assert len(result) == 3
    assert result[0] == 45.2
    assert result[1] == 43.8
    assert result[2] == 44.1

    # Verify correct API call was made
    mock_post.assert_called_once()
    call_args = mock_post.call_args

    # Check URL (FastAPI, not Databricks)
    assert "forecast" in call_args[0][0]  # URL contains /forecast

    # Check headers (X-API-Key, not Authorization)
    assert "X-API-Key" in call_args[1]["headers"]
    # FIXED: Check against the mocked value
    assert call_args[1]["headers"]["X-API-Key"] == "test-api-key-from-mock"

    # Check params (product_id and horizon)
    assert call_args[1]["params"]["product_id"] == "Cat1"
    assert call_args[1]["params"]["horizon"] == 14


@patch("app.requests.post")
def test_get_forecast_different_horizons(mock_post):
    """Test forecast API with different horizon values"""
    from app import get_forecast

    # Test with horizon = 7
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "product": {"id": "Cat1", "name": "WHITE HANGING HEART T-LIGHT HOLDER"},
        "forecast": {"horizon_days": 7, "values": [45.2, 43.8, 44.1, 46.0, 45.5, 44.8, 45.3]},
        "generated_at": "2026-07-03T10:30:00Z",
    }
    mock_post.return_value = mock_response

    result = get_forecast("Cat1", 7)
    assert len(result) == 7

    # Test with horizon = 30
    mock_response.json.return_value = {
        "success": True,
        "product": {"id": "Cat2", "name": "JUMBO BAG RED RETROSPOT"},
        "forecast": {"horizon_days": 30, "values": [10.0] * 30},
        "generated_at": "2026-07-03T10:30:00Z",
    }
    result = get_forecast("Cat2", 30)
    assert len(result) == 30
    assert all(v == 10.0 for v in result)


@patch("app.requests.post")
def test_get_forecast_invalid_api_key(mock_post):
    """Test forecast API with invalid API key (401)"""
    from app import get_forecast

    # Mock 401 Unauthorized response
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Invalid API key"
    mock_post.return_value = mock_response

    with patch("app.st.error"):  # Mock st.error to avoid errors
        result = get_forecast("Cat1", 14)

    # Should return None on 401
    assert result is None


@patch("app.requests.post")
def test_get_forecast_product_not_found(mock_post):
    """Test forecast API with non-existent product (404)"""
    from app import get_forecast

    # Mock 404 Not Found response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Product not found"
    mock_post.return_value = mock_response

    with patch("app.st.error"):
        result = get_forecast("InvalidProduct", 14)

    # Should return None on 404
    assert result is None


@patch("app.requests.post")
def test_get_forecast_api_error(mock_post):
    """Test forecast API with server error (500)"""
    from app import get_forecast

    # Mock 500 server error
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_post.return_value = mock_response

    with patch("app.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None on 500
    assert result is None


@patch("app.requests.post")
def test_get_forecast_connection_error(mock_post):
    """Test forecast API with connection error"""
    from app import get_forecast

    # Mock connection error
    mock_post.side_effect = Exception("Connection refused")

    with patch("app.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None on connection error
    assert result is None


@patch("app.requests.post")
def test_get_forecast_timeout(mock_post):
    """Test forecast API with timeout"""
    from app import get_forecast
    import requests

    # Mock timeout error
    mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

    with patch("app.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None on timeout
    assert result is None


@patch("app.requests.post")
def test_get_forecast_malformed_response(mock_post):
    """Test forecast API with malformed JSON response"""
    from app import get_forecast

    # Mock response with invalid JSON structure
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        # Missing 'forecast' key
        "product": {"id": "Cat1"},
    }
    mock_post.return_value = mock_response

    with patch("app.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None when response structure is invalid
    assert result is None


@patch("app.requests.post")
def test_get_forecast_empty_values(mock_post):
    """Test forecast API with empty forecast values"""
    from app import get_forecast

    # Mock response with empty forecast values
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "product": {"id": "Cat1", "name": "WHITE HANGING HEART T-LIGHT HOLDER"},
        "forecast": {"horizon_days": 14, "values": []},
        "generated_at": "2026-07-03T10:30:00Z",
    }
    mock_post.return_value = mock_response

    result = get_forecast("Cat1", 14)

    # Should handle empty values gracefully
    assert result is not None
    assert len(result) == 0


def test_products_config():
    """Test product configuration (NEW)"""
    from app import PRODUCTS

    # Should have 2 products configured
    assert len(PRODUCTS) == 2
    assert "Cat1" in PRODUCTS
    assert "Cat2" in PRODUCTS

    # Check product structure
    assert "name" in PRODUCTS["Cat1"]
    assert "product_id" in PRODUCTS["Cat1"]

    # Check specific products
    assert PRODUCTS["Cat1"]["name"] == "WHITE HANGING HEART T-LIGHT HOLDER"
    assert PRODUCTS["Cat2"]["name"] == "JUMBO BAG RED RETROSPOT"


def test_products_structure():
    """Test all products have required fields"""
    from app import PRODUCTS

    required_fields = ["name", "sku", "product_id", "color"]

    for product_id, product_data in PRODUCTS.items():
        for field in required_fields:
            assert field in product_data, f"Product {product_id} missing required field: {field}"
        
        # Validate product_id matches key
        assert product_data["product_id"] == product_id
        
        # Validate color is hex format
        assert product_data["color"].startswith("#")
        assert len(product_data["color"]) == 7  # #RRGGBB format


def test_fastapi_url_config():
    """Test FastAPI URL configuration (NEW: replaces test_databricks_host_config)"""
    from app import FASTAPI_URL

    # Should be configured (from mock or default)
    assert FASTAPI_URL is not None
    assert isinstance(FASTAPI_URL, str)

    # Should be a valid URL format
    assert FASTAPI_URL.startswith("http://") or FASTAPI_URL.startswith("https://")


def test_api_key_config():
    """Test API key configuration (NEW)"""
    from app import API_KEY

    # Should be configured (from mock or default)
    assert API_KEY is not None
    assert isinstance(API_KEY, str)
    assert len(API_KEY) > 0


def test_config_values_are_strings():
    """Test that all config values are proper strings, not MagicMock objects"""
    from app import FASTAPI_URL, API_KEY

    # Ensure they're actual strings, not MagicMock instances
    assert type(FASTAPI_URL).__name__ == "str"
    assert type(API_KEY).__name__ == "str"
    
    # Verify they can be used in string operations
    assert "http" in FASTAPI_URL.lower()
    assert len(API_KEY) > 5


@patch("app.time.sleep")
@patch("app.requests.get")
def test_keep_fastapi_warm_success(mock_get, mock_sleep):
    """Test keep_fastapi_warm function with successful ping"""
    from app import keep_fastapi_warm

    # Mock successful health check
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Run one iteration (mock sleep to exit after first ping)
    mock_sleep.side_effect = [None, KeyboardInterrupt]  # Exit after first iteration

    try:
        keep_fastapi_warm()
    except KeyboardInterrupt:
        pass

    # Verify health endpoint was called
    mock_get.assert_called()
    assert "health" in mock_get.call_args[0][0]


@patch("app.time.sleep")
@patch("app.requests.get")
def test_keep_fastapi_warm_handles_errors(mock_get, mock_sleep):
    """Test keep_fastapi_warm handles connection errors gracefully"""
    from app import keep_fastapi_warm

    # Mock connection error
    mock_get.side_effect = Exception("Connection failed")
    mock_sleep.side_effect = [None, KeyboardInterrupt]

    try:
        keep_fastapi_warm()
    except KeyboardInterrupt:
        pass

    # Should not crash, error should be caught
    mock_get.assert_called()


def test_imports_available():
    """Test that all required imports are available"""
    # These imports should not raise errors
    from app import PRODUCTS, FASTAPI_URL, API_KEY
    from app import get_forecast, calculate_stock_recommendation

    # Verify they're all defined
    assert PRODUCTS is not None
    assert FASTAPI_URL is not None
    assert API_KEY is not None
    assert callable(get_forecast)
    assert callable(calculate_stock_recommendation)


def test_pytest_guard_prevents_streamlit_code():
    """Test that pytest guard prevents Streamlit UI code from running"""
    import sys
    
    # Verify pytest is detected
    assert "pytest" in sys.modules
    
    # Verify streamlit is our mock
    import streamlit as st
    assert type(st).__name__ == "MagicMock"
