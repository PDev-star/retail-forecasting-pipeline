# test_api_client.py - Unit tests for API Client Service
"""
Test services.api_client module - mocks services.api_client.requests
Tests get_forecast() FastAPI integration.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock streamlit before importing
mock_st = MagicMock()
mock_st.secrets.get.side_effect = lambda key, default=None: {
    "fastapi_url": "http://localhost:8000",
    "api_key": "test-api-key-from-mock"
}.get(key, default)
sys.modules["streamlit"] = mock_st

from services.api_client import get_forecast


@patch("services.api_client.requests.post")
def test_get_forecast_success(mock_post):
    """Test successful forecast API call via FastAPI gateway"""
    # Mock FastAPI response format
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "product": {"id": "Cat1", "name": "WHITE HANGING HEART T-LIGHT HOLDER"},
        "forecast": {"horizon_days": 14, "values": [45.2, 43.8, 44.1]},
        "generated_at": "2026-07-03T10:30:00Z",
    }
    mock_post.return_value = mock_response

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
    assert call_args[1]["headers"]["X-API-Key"] == "test-api-key-from-mock"

    # Check params (product_id and horizon)
    assert call_args[1]["params"]["product_id"] == "Cat1"
    assert call_args[1]["params"]["horizon"] == 14


@patch("services.api_client.requests.post")
def test_get_forecast_different_horizons(mock_post):
    """Test forecast API with different horizon values"""
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


@patch("services.api_client.requests.post")
def test_get_forecast_invalid_api_key(mock_post):
    """Test forecast API with invalid API key (401)"""
    # Mock 401 Unauthorized response
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Invalid API key"
    mock_post.return_value = mock_response

    with patch("services.api_client.st.error"):  # Mock st.error to avoid errors
        result = get_forecast("Cat1", 14)

    # Should return None on 401
    assert result is None


@patch("services.api_client.requests.post")
def test_get_forecast_product_not_found(mock_post):
    """Test forecast API with non-existent product (404)"""
    # Mock 404 Not Found response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Product not found"
    mock_post.return_value = mock_response

    with patch("services.api_client.st.error"):
        result = get_forecast("InvalidProduct", 14)

    # Should return None on 404
    assert result is None


@patch("services.api_client.requests.post")
def test_get_forecast_api_error(mock_post):
    """Test forecast API with server error (500)"""
    # Mock 500 server error
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_post.return_value = mock_response

    with patch("services.api_client.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None on 500
    assert result is None


@patch("services.api_client.requests.post")
def test_get_forecast_connection_error(mock_post):
    """Test forecast API with connection error"""
    # Mock connection error
    mock_post.side_effect = Exception("Connection refused")

    with patch("services.api_client.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None on connection error
    assert result is None


@patch("services.api_client.requests.post")
def test_get_forecast_timeout(mock_post):
    """Test forecast API with timeout"""
    import requests

    # Mock timeout error
    mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

    with patch("services.api_client.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None on timeout
    assert result is None


@patch("services.api_client.requests.post")
def test_get_forecast_malformed_response(mock_post):
    """Test forecast API with malformed JSON response"""
    # Mock response with invalid JSON structure
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        # Missing 'forecast' key
        "product": {"id": "Cat1"},
    }
    mock_post.return_value = mock_response

    with patch("services.api_client.st.error"):
        result = get_forecast("Cat1", 14)

    # Should return None when response structure is invalid
    assert result is None


@patch("services.api_client.requests.post")
def test_get_forecast_empty_values(mock_post):
    """Test forecast API with empty forecast values"""
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
