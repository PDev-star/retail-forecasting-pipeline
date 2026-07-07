# test_app.py - Unit tests for Streamlit App (FastAPI Proxy Architecture)
import os
import sys
from unittest.mock import MagicMock, patch

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
