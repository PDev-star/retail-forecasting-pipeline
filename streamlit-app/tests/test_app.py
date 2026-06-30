# test_app.py - Unit tests for Streamlit App
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock streamlit before importing app
sys.modules["streamlit"] = MagicMock()

# Import functions from app


def test_calculate_stock_recommendation():
    """Test stock recommendation calculation"""
    from app import calculate_stock_recommendation

    forecast = [10, 12, 11, 13, 10, 12, 11, 13, 10, 12, 11, 13, 10, 12]

    # Test with default parameters
    result = calculate_stock_recommendation(
        forecast, lead_time_days=14, safety_factor=1.2
    )

    expected_lead_time_demand = sum(forecast[:14])  # 160
    expected_recommended = int(expected_lead_time_demand * 1.2)  # 192

    assert result == expected_recommended


def test_calculate_stock_recommendation_custom_lead_time():
    """Test stock recommendation with custom lead time"""
    from app import calculate_stock_recommendation

    forecast = [10] * 30  # 30 days of 10 units/day

    result = calculate_stock_recommendation(
        forecast, lead_time_days=7, safety_factor=1.5
    )

    expected_lead_time_demand = 10 * 7  # 70
    expected_recommended = int(70 * 1.5)  # 105

    assert result == expected_recommended


@patch("app.requests.post")
def test_get_forecast_success(mock_post):
    """Test successful forecast API call"""
    from app import get_forecast

    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "predictions": [{"AutoETS": 45.2}, {"AutoETS": 43.8}, {"AutoETS": 44.1}]
    }
    mock_post.return_value = mock_response

    # Mock Streamlit secrets
    with patch("app.st.secrets", {"databricks_token": "test-token"}):
        result = get_forecast("Cat1Forecast", 14)

    assert result is not None
    assert len(result) == 3
    assert result[0] == 45.2


@patch("app.requests.post")
def test_get_forecast_api_error(mock_post):
    """Test forecast API error handling"""
    from app import get_forecast

    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"
    mock_post.return_value = mock_response

    with patch("app.st.secrets", {"databricks_token": "test-token"}):
        with patch("app.st.error"):  # Mock st.error to avoid errors
            result = get_forecast("Cat1Forecast", 14)

    assert result is None


def test_products_config():
    """Test products configuration"""
    from app import PRODUCTS

    assert "Cat1" in PRODUCTS
    assert "Cat2" in PRODUCTS
    assert PRODUCTS["Cat1"]["endpoint"] == "Cat1Forecast"
    assert PRODUCTS["Cat2"]["endpoint"] == "Cat2Forecast"


def test_databricks_host_config():
    """Test Databricks host configuration"""
    from app import DATABRICKS_HOST

    assert DATABRICKS_HOST.startswith("https://")
    assert "databricks.com" in DATABRICKS_HOST
