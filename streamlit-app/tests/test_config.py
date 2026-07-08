# test_config.py - Unit tests for Configuration Module
"""
Test utils.config module - mocks utils.config.requests for keep_alive tests
Tests PRODUCTS, FASTAPI_URL, API_KEY, and keep_fastapi_warm().
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

from utils.config import PRODUCTS, FASTAPI_URL, API_KEY, keep_fastapi_warm


def test_products_config():
    """Test product configuration"""
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
    """Test FastAPI URL configuration"""
    # Should be configured (from mock or default)
    assert FASTAPI_URL is not None
    assert isinstance(FASTAPI_URL, str)

    # Should be a valid URL format
    assert FASTAPI_URL.startswith("http://") or FASTAPI_URL.startswith("https://")


def test_api_key_config():
    """Test API key configuration"""
    # Should be configured (from mock or default)
    assert API_KEY is not None
    assert isinstance(API_KEY, str)
    assert len(API_KEY) > 0


def test_config_values_are_strings():
    """Test that all config values are proper strings, not MagicMock objects"""
    # Ensure they're actual strings, not MagicMock instances
    assert type(FASTAPI_URL).__name__ == "str"
    assert type(API_KEY).__name__ == "str"
    
    # Verify they can be used in string operations
    assert "http" in FASTAPI_URL.lower()
    assert len(API_KEY) > 5


@patch("utils.config.time.sleep")
@patch("utils.config.requests.get")
def test_keep_fastapi_warm_success(mock_get, mock_sleep):
    """Test keep_fastapi_warm function with successful ping"""
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


@patch("utils.config.time.sleep")
@patch("utils.config.requests.get")
def test_keep_fastapi_warm_handles_errors(mock_get, mock_sleep):
    """Test keep_fastapi_warm handles connection errors gracefully"""
    # Mock connection error
    mock_get.side_effect = Exception("Connection refused")

    # Mock sleep to exit after first attempt
    mock_sleep.side_effect = [None, KeyboardInterrupt]

    try:
        keep_fastapi_warm()
    except KeyboardInterrupt:
        pass

    # Should not crash, just log error
    mock_get.assert_called()
