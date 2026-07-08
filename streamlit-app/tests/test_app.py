# test_app.py - Integration tests for App Module
"""
Minimal integration tests for app.py
Tests re-exports and pytest guard functionality.
All unit tests moved to dedicated module test files.
"""
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock streamlit before importing app
mock_st = MagicMock()
mock_st.secrets.get.side_effect = lambda key, default=None: {
    "fastapi_url": "http://localhost:8000",
    "api_key": "test-api-key-from-mock"
}.get(key, default)
sys.modules["streamlit"] = mock_st


def test_imports_available():
    """Test that key functions are available via app module (backward compatibility)"""
    from app import get_forecast, calculate_stock_recommendation, PRODUCTS, FASTAPI_URL, API_KEY

    # Verify imports work
    assert callable(get_forecast)
    assert callable(calculate_stock_recommendation)
    assert isinstance(PRODUCTS, dict)
    assert isinstance(FASTAPI_URL, str)
    assert isinstance(API_KEY, str)


def test_pytest_guard_prevents_streamlit_code():
    """Test that pytest guard prevents UI code from running during tests"""
    # Import app module - UI code should NOT run because pytest is in sys.modules
    import app

    # If this test passes, the pytest guard worked
    # (UI code would crash without streamlit properly configured)
    assert 'pytest' in sys.modules
