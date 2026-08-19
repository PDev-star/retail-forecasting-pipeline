# test_tabs.py - Unit tests for tab rendering components
"""
Tests for all tab rendering functions:
- render_forecast_tab
- render_data_tab  
- render_stock_tab
- render_insights_tab
- render_gemini_tab (NEW)
- render_welcome_screen

Focus: Integration tests to verify imports and signatures, not deep mocking.
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


# ============================================================================
# INTEGRATION TEST: All tabs import successfully
# ============================================================================

def test_all_tabs_import(mock_streamlit):
    """Test that all tab functions can be imported"""
    from components.tabs import (
        render_forecast_tab,
        render_data_tab,
        render_stock_tab,
        render_insights_tab,
        render_gemini_tab,
        render_welcome_screen
    )
    
    # Verify all are callable
    assert callable(render_forecast_tab)
    assert callable(render_data_tab)
    assert callable(render_stock_tab)
    assert callable(render_insights_tab)
    assert callable(render_gemini_tab)  # NEW!
    assert callable(render_welcome_screen)


def test_render_gemini_tab_signature(mock_streamlit):
    """Test render_gemini_tab has correct signature"""
    from components.tabs import render_gemini_tab
    import inspect
    
    sig = inspect.signature(render_gemini_tab)
    params = list(sig.parameters.keys())
    
    # render_gemini_tab() takes no parameters (standalone tab)
    assert len(params) == 0


def test_render_insights_tab_signature(mock_streamlit):
    """Test render_insights_tab has correct signature"""
    from components.tabs import render_insights_tab
    import inspect
    
    sig = inspect.signature(render_insights_tab)
    params = list(sig.parameters.keys())
    
    # Should have forecast, product, scenario_desc, lead_time_days, calculate_stock_recommendation
    assert "forecast" in params
    assert "product" in params
    assert "scenario_desc" in params
    assert "lead_time_days" in params
    assert "calculate_stock_recommendation" in params


def test_render_stock_tab_signature(mock_streamlit):
    """Test render_stock_tab has correct signature"""
    from components.tabs import render_stock_tab
    import inspect
    
    sig = inspect.signature(render_stock_tab)
    params = list(sig.parameters.keys())
    
    assert "forecast" in params
    assert "lead_time_days" in params
    assert "calculate_stock_recommendation" in params


def test_render_data_tab_signature(mock_streamlit):
    """Test render_data_tab has correct signature"""
    from components.tabs import render_data_tab
    import inspect
    
    sig = inspect.signature(render_data_tab)
    params = list(sig.parameters.keys())
    
    assert "df_forecast" in params
    assert "product" in params


def test_render_forecast_tab_signature(mock_streamlit):
    """Test render_forecast_tab has correct signature"""
    from components.tabs import render_forecast_tab
    import inspect
    
    sig = inspect.signature(render_forecast_tab)
    params = list(sig.parameters.keys())
    
    assert "forecast" in params
    assert "horizon" in params
    assert "product" in params
    assert "scenario_desc" in params


def test_render_welcome_screen_signature(mock_streamlit):
    """Test render_welcome_screen has correct signature"""
    from components.tabs import render_welcome_screen
    import inspect
    
    sig = inspect.signature(render_welcome_screen)
    params = list(sig.parameters.keys())
    
    # Should take no parameters
    assert len(params) == 0


# ============================================================================
# COVERAGE: Verify new tab is exported and documented
# ============================================================================

def test_gemini_tab_is_new_addition(mock_streamlit):
    """Verify render_gemini_tab is the NEW tab we added"""
    from components.tabs import render_gemini_tab
    
    # Verify docstring mentions it's for Gemini
    assert render_gemini_tab.__doc__ is not None
    assert "gemini" in render_gemini_tab.__doc__.lower() or "scenario" in render_gemini_tab.__doc__.lower()


def test_insights_tab_is_real_time(mock_streamlit):
    """Verify render_insights_tab is for real-time AI insights"""
    from components.tabs import render_insights_tab
    
    # Verify docstring mentions real-time or Groq
    assert render_insights_tab.__doc__ is not None
    assert "real-time" in render_insights_tab.__doc__.lower() or "groq" in render_insights_tab.__doc__.lower()
