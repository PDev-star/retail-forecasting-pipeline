# test_tabs_comprehensive.py - Comprehensive coverage tests for all tab functions
"""
Comprehensive tests to achieve 80%+ coverage for components/tabs.py
Tests all UI rendering paths including error cases and edge conditions.
"""
import os
import sys
from unittest.mock import MagicMock, patch, mock_open
import pytest
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def mock_streamlit():
    """Comprehensive mock for streamlit with all required methods"""
    mock_st = MagicMock()
    
    # Mock UI components
    mock_st.markdown = MagicMock()
    mock_st.write = MagicMock()
    mock_st.info = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.error = MagicMock()
    mock_st.success = MagicMock()
    mock_st.caption = MagicMock()
    mock_st.dataframe = MagicMock()
    mock_st.download_button = MagicMock()
    mock_st.metric = MagicMock()
    mock_st.text_area = MagicMock(return_value="")
    mock_st.button = MagicMock(return_value=False)
    mock_st.spinner = MagicMock(return_value=MagicMock(__enter__=lambda x: x, __exit__=lambda *args: None))
    
    # Mock columns and expander
    mock_col = MagicMock()
    mock_col.__enter__ = lambda x: x
    mock_col.__exit__ = lambda *args: None
    mock_st.columns = MagicMock(return_value=[mock_col, mock_col])
    
    mock_exp = MagicMock()
    mock_exp.__enter__ = lambda x: x
    mock_exp.__exit__ = lambda *args: None
    mock_st.expander = MagicMock(return_value=mock_exp)
    
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        yield mock_st


# ============================================================================
# DATA TAB TESTS (render_data_tab) - Lines 35-54
# ============================================================================

def test_render_data_tab_displays_table(mock_streamlit):
    """Test data tab renders dataframe with formatting"""
    from components.tabs import render_data_tab
    
    # Create test dataframe
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=5),
        'Predicted Demand': [100, 110, 120, 115, 105]
    })
    product = {'name': 'Test Product', 'sku': 'TST001'}
    
    with patch('components.tabs.st', mock_streamlit):
        render_data_tab(df, product)
    
    # Verify markdown header was called
    assert mock_streamlit.markdown.called
    # Verify dataframe was displayed
    assert mock_streamlit.dataframe.called


def test_render_data_tab_download_button(mock_streamlit):
    """Test data tab includes CSV download button"""
    from components.tabs import render_data_tab
    
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=3),
        'Predicted Demand': [100, 110, 120]
    })
    product = {'name': 'Widget', 'sku': 'WDG123'}
    
    with patch('components.tabs.st', mock_streamlit):
        render_data_tab(df, product)
    
    # Verify download button was created
    assert mock_streamlit.download_button.called
    call_args = mock_streamlit.download_button.call_args
    assert 'CSV' in call_args[1].get('label', '')
    assert product['sku'] in call_args[1].get('file_name', '')


# ============================================================================
# STOCK TAB TESTS (render_stock_tab) - Lines 59-100
# ============================================================================

def test_render_stock_tab_calculates_metrics(mock_streamlit):
    """Test stock tab calculates and displays all metrics"""
    from components.tabs import render_stock_tab
    
    forecast = [100, 110, 120, 115, 105]
    lead_time_days = 5
    
    def mock_calc_stock(forecast, lead_time):
        return int(sum(forecast[:lead_time]) * 1.2)
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('components.tabs.render_inventory_chart'):
            render_stock_tab(forecast, lead_time_days, mock_calc_stock)
    
    # Verify markdown header
    assert mock_streamlit.markdown.called
    # Verify metrics were displayed (4 metrics total)
    assert mock_streamlit.metric.call_count == 4
    # Verify columns were created
    assert mock_streamlit.columns.called


def test_render_stock_tab_renders_chart(mock_streamlit):
    """Test stock tab renders inventory chart"""
    from components.tabs import render_stock_tab
    
    forecast = [100, 110, 120]
    lead_time_days = 3
    
    def mock_calc(f, l):
        return 350
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('components.tabs.render_inventory_chart') as mock_chart:
            render_stock_tab(forecast, lead_time_days, mock_calc)
            
            # Verify inventory chart was called
            assert mock_chart.called


# ============================================================================
# GEMINI TAB TESTS (render_gemini_tab) - Lines 105-139
# ============================================================================

def test_render_gemini_tab_success_response(mock_streamlit):
    """Test Gemini tab displays insights on successful API response"""
    from components.tabs import render_gemini_tab
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "total": 2,
        "insights": [
            {
                "scenario_id": 1,
                "scenario_name": "Model Performance",
                "question": "How accurate is the model?",
                "explanation": "The model achieves 95% accuracy.",
                "context_table": "workspace.default.metrics",
                "generated_at": "2026-08-10T12:00:00"
            },
            {
                "scenario_id": 2,
                "scenario_name": "Risk Analysis",
                "question": "What are the risks?",
                "explanation": "Main risk is demand volatility.",
                "context_table": "workspace.default.risks",
                "generated_at": "2026-08-10T12:00:00"
            }
        ]
    }
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('requests.get', return_value=mock_response):
            render_gemini_tab()
    
    # Verify headers displayed
    assert mock_streamlit.markdown.call_count >= 3
    # Verify expanders created for scenarios
    assert mock_streamlit.expander.call_count >= 2
    # Verify success message shown
    assert mock_streamlit.success.called


def test_render_gemini_tab_empty_insights(mock_streamlit):
    """Test Gemini tab handles empty insights gracefully"""
    from components.tabs import render_gemini_tab
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "total": 0,
        "insights": []
    }
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('requests.get', return_value=mock_response):
            render_gemini_tab()
    
    # Verify warning is shown
    assert mock_streamlit.warning.called


def test_render_gemini_tab_http_error(mock_streamlit):
    """Test Gemini tab handles HTTP errors"""
    from components.tabs import render_gemini_tab
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('requests.get', return_value=mock_response):
            render_gemini_tab()
    
    # Verify error message shown
    assert mock_streamlit.error.called


def test_render_gemini_tab_connection_error(mock_streamlit):
    """Test Gemini tab handles connection errors"""
    from components.tabs import render_gemini_tab
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('requests.get', side_effect=Exception("Connection refused")):
            render_gemini_tab()
    
    # Verify error and info messages shown
    assert mock_streamlit.error.called
    assert mock_streamlit.info.called


# ============================================================================
# INSIGHTS TAB CUSTOM Q&A TESTS - Lines 212-229
# ============================================================================

def test_render_insights_tab_custom_qna_no_button_click(mock_streamlit):
    """Test custom Q&A section when button not clicked"""
    from components.tabs import render_insights_tab
    
    forecast = [100, 110, 120]
    product = {'name': 'Test', 'sku': 'T1', 'product_id': 'p1'}
    scenario_desc = 'Normal'
    lead_time_days = 5
    
    def mock_calc(f, l):
        return 350
    
    # Button returns False (not clicked)
    mock_streamlit.button.return_value = False
    mock_streamlit.text_area.return_value = "Test question"
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('utils.ai_insights_groq.get_forecast_insight', return_value="AI insight"):
            with patch('utils.ai_insights_groq.get_stock_insight', return_value="AI insight"):
                with patch('utils.ai_insights_groq.get_risk_insight', return_value="AI insight"):
                    with patch('utils.ai_insights_groq.get_custom_ai_answer') as mock_custom:
                        render_insights_tab(forecast, product, scenario_desc, lead_time_days, mock_calc)
                        
                        # Custom AI should NOT be called when button not clicked
                        mock_custom.assert_not_called()


def test_render_insights_tab_custom_qna_button_clicked_with_question(mock_streamlit):
    """Test custom Q&A executes when button clicked with valid question"""
    from components.tabs import render_insights_tab
    
    forecast = [100, 110, 120]
    product = {'name': 'Test', 'sku': 'T1', 'product_id': 'p1'}
    scenario_desc = 'Normal'
    lead_time_days = 5
    
    def mock_calc(f, l):
        return 350
    
    # Button returns True (clicked), question provided
    mock_streamlit.button.return_value = True
    mock_streamlit.text_area.return_value = "Should I increase orders?"
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('utils.ai_insights_groq.get_forecast_insight', return_value="AI"):
            with patch('utils.ai_insights_groq.get_stock_insight', return_value="AI"):
                with patch('utils.ai_insights_groq.get_risk_insight', return_value="AI"):
                    with patch('utils.ai_insights_groq.get_custom_ai_answer', return_value="Yes, increase by 20%") as mock_custom:
                        render_insights_tab(forecast, product, scenario_desc, lead_time_days, mock_calc)
                        
                        # Custom AI SHOULD be called
                        mock_custom.assert_called_once()
                        # Verify success and info messages shown
                        assert mock_streamlit.success.called
                        assert mock_streamlit.info.called


def test_render_insights_tab_custom_qna_button_clicked_no_question(mock_streamlit):
    """Test custom Q&A shows warning when button clicked without question"""
    from components.tabs import render_insights_tab
    
    forecast = [100, 110, 120]
    product = {'name': 'Test', 'sku': 'T1', 'product_id': 'p1'}
    scenario_desc = 'Normal'
    lead_time_days = 5
    
    def mock_calc(f, l):
        return 350
    
    # Button returns True but empty question
    mock_streamlit.button.return_value = True
    mock_streamlit.text_area.return_value = "   "  # Only whitespace
    
    with patch('components.tabs.st', mock_streamlit):
        with patch('utils.ai_insights_groq.get_forecast_insight', return_value="AI"):
            with patch('utils.ai_insights_groq.get_stock_insight', return_value="AI"):
                with patch('utils.ai_insights_groq.get_risk_insight', return_value="AI"):
                    with patch('utils.ai_insights_groq.get_custom_ai_answer') as mock_custom:
                        render_insights_tab(forecast, product, scenario_desc, lead_time_days, mock_calc)
                        
                        # Custom AI should NOT be called with empty question
                        mock_custom.assert_not_called()
                        # Verify warning shown
                        assert mock_streamlit.warning.called
