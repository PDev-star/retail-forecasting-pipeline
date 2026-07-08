# test_app.py - Integration tests for App Module
"""
Minimal integration tests for app.py
Tests re-exports and pytest guard functionality.
All unit tests moved to dedicated module test files.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def mock_streamlit():
    """Mock streamlit only for tests in this file, doesn't pollute sys.modules globally"""
    mock_st = MagicMock()
    mock_st.secrets.get.side_effect = lambda key, default=None: {
        "fastapi_url": "http://localhost:8000",
        "api_key": "test-api-key-from-mock"
    }.get(key, default)
    
    # Use patch.dict to temporarily mock streamlit in sys.modules
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        yield mock_st


def test_imports_available(mock_streamlit):
    """Test that key functions are available via app module (backward compatibility)"""
    from app import get_forecast, calculate_stock_recommendation, PRODUCTS, FASTAPI_URL, API_KEY

    # Verify imports work
    assert callable(get_forecast)
    assert callable(calculate_stock_recommendation)
    assert isinstance(PRODUCTS, dict)
    assert FASTAPI_URL is not None
    assert API_KEY is not None


def test_products_structure(mock_streamlit):
    """Test PRODUCTS data structure"""
    from app import PRODUCTS

    assert len(PRODUCTS) > 0
    for product_id, product in PRODUCTS.items():
        assert "name" in product
        assert "category" in product
        assert "current_stock" in product
        assert "safety_stock" in product


def test_forecast_function_signature(mock_streamlit):
    """Test that get_forecast has correct signature"""
    from app import get_forecast
    import inspect

    sig = inspect.signature(get_forecast)
    params = list(sig.parameters.keys())
    
    assert "product" in params
    assert "horizon" in params


def test_stock_recommendation_signature(mock_streamlit):
    """Test that calculate_stock_recommendation has correct signature"""
    from app import calculate_stock_recommendation
    import inspect

    sig = inspect.signature(calculate_stock_recommendation)
    params = list(sig.parameters.keys())
    
    assert "product" in params
    assert "forecast_data" in params
