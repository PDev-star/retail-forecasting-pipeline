# test_tabs.py - Unit tests for tab rendering components
"""
Tests for all tab rendering functions - Focus on integration tests.
"""
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def mock_streamlit():
    """Mock streamlit module for all tests"""
    mock_st = MagicMock()
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        yield mock_st

def test_all_tabs_import(mock_streamlit):
    """Test that all tab functions can be imported"""
    from components.tabs import (
        render_forecast_tab, render_data_tab, render_stock_tab,
        render_insights_tab, render_gemini_tab, render_welcome_screen
    )
    assert callable(render_forecast_tab)
    assert callable(render_gemini_tab)  # NEW!

def test_render_gemini_tab_signature(mock_streamlit):
    """Test render_gemini_tab has correct signature"""
    from components.tabs import render_gemini_tab
    import inspect
    sig = inspect.signature(render_gemini_tab)
    assert len(list(sig.parameters.keys())) == 0

def test_render_gemini_tab_loads_without_crash(mock_streamlit):
    """Test that Gemini tab renders without crashing"""
    from components.tabs import render_gemini_tab
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True, "total": 3,
        "insights": [
            {"scenario_id": 1, "scenario_name": "Test", "question": "Q", 
             "explanation": "E", "context_table": "t", "generated_at": "2026-01-01"}
        ]
    }
    with patch('requests.get', return_value=mock_response):
        render_gemini_tab()
    assert True
