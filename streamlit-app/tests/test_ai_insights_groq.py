"""
Unit tests for AI Insights module (utils/ai_insights_groq.py)
Tests all AI-powered functions: forecast, stock, risk, and custom Q&A
Groq API version (single key, no rotation)
"""

import pytest
from unittest.mock import patch, MagicMock
from utils import ai_insights_groq
from utils.ai_insights_groq import (
    get_forecast_insight,
    get_stock_insight,
    get_risk_insight,
    get_custom_ai_answer,
    _call_groq
)


# ============================================================================
# TEST GROUP 1: FALLBACK TESTS (No API keys needed!)
# ============================================================================

def test_forecast_insight_fallback():
    """When API unavailable, get_forecast_insight returns text fallback."""
    
    # Clear API key to force fallback
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'forecast': [100, 105, 110, 115, 120],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        # Check fallback returns useful content
        assert "Forecast Summary" in result or "demand" in result.lower()
        assert "110.0" in result  # Average demand
        assert "increasing" in result.lower()


def test_stock_insight_fallback():
    """When API unavailable, get_stock_insight returns text fallback."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'recommended_stock': 500,
            'reorder_point': 200,
            'safety_stock': 100,
            'lead_time_days': 5
        }
        
        result = get_stock_insight(data)
        
        assert "Stock Recommendation" in result or "500" in result
        assert "reorder" in result.lower()


def test_risk_insight_fallback():
    """When API unavailable, get_risk_insight returns text fallback."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'volatility': 50,
            'avg_demand': 100,
            'trend': 'increasing',
            'scenario': 'Normal'
        }
        
        result = get_risk_insight(data)
        
        assert "Risk Assessment" in result or "volatility" in result.lower()
        assert "50.0%" in result  # Volatility ratio


def test_custom_ai_answer_no_key():
    """When no API key configured, custom Q&A returns helpful error message."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        context = {
            'forecast': [100, 105],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal',
            'stock_data': {'recommended_stock': 500}
        }
        
        result = get_custom_ai_answer("How much should I order?", context)
        
        assert "unavailable" in result.lower() or "api key" in result.lower()
        assert "GROQ_API_KEY" in result


# ============================================================================
# TEST GROUP 2: EDGE CASES (Unusual inputs)
# ============================================================================

def test_insights_with_empty_forecast():
    """AI insights handle empty forecast gracefully."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'forecast': [],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "no forecast" in result.lower() or "unavailable" in result.lower()


def test_insights_with_single_value_forecast():
    """AI insights handle single-value forecast."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'forecast': [100],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "100.0" in result  # Average demand
        assert "stable" in result.lower()  # Single value = stable trend


# ============================================================================
# TEST GROUP 3: GROQ API MOCK TESTS (Simulated API calls)
# ============================================================================

def test_call_groq_success():
    """Test Groq API succeeds."""
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "AI-generated insight about demand patterns."
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_completion
            mock_groq_class.return_value = mock_client
            
            result = _call_groq("Test prompt")
            
            assert result == "AI-generated insight about demand patterns."
            mock_client.chat.completions.create.assert_called_once()


def test_call_groq_api_failure():
    """Test Groq API returns None when it fails."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_groq_class.return_value = mock_client
            
            result = _call_groq("Test prompt")
            
            assert result is None


# ============================================================================
# TEST GROUP 4: FULL INSIGHT FUNCTION TESTS (With mocked API)
# ============================================================================

def test_get_forecast_insight_with_successful_api():
    """Test get_forecast_insight returns AI-generated text when API works."""
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Your demand is trending upward. Stock up now!"
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_completion
            mock_groq_class.return_value = mock_client
            
            data = {
                'forecast': [100, 110, 120],
                'product': {'name': 'Widget', 'sku': 'W001'},
                'scenario': 'Normal'
            }
            
            result = get_forecast_insight(data)
            
            assert result == "Your demand is trending upward. Stock up now!"


def test_get_forecast_insight_with_failed_api():
    """Test get_forecast_insight returns fallback when API fails."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_groq_class.return_value = mock_client
            
            data = {
                'forecast': [100, 110, 120],
                'product': {'name': 'Widget', 'sku': 'W001'},
                'scenario': 'Normal'
            }
            
            result = get_forecast_insight(data)
            
            # Should return fallback text
            assert "110.0" in result  # Average demand
            assert "increasing" in result.lower()


def test_get_stock_insight_with_successful_api():
    """Test get_stock_insight returns AI text when API works."""
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "This order size ensures 5 days of buffer stock."
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_completion
            mock_groq_class.return_value = mock_client
            
            data = {
                'recommended_stock': 500,
                'reorder_point': 200,
                'safety_stock': 100,
                'lead_time_days': 5
            }
            
            result = get_stock_insight(data)
            
            assert result == "This order size ensures 5 days of buffer stock."


def test_get_risk_insight_with_successful_api():
    """Test get_risk_insight returns AI text when API works."""
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "High volatility detected. Increase safety stock by 20%."
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_completion
            mock_groq_class.return_value = mock_client
            
            data = {
                'volatility': 60,
                'avg_demand': 100,
                'trend': 'increasing',
                'scenario': 'Spike'
            }
            
            result = get_risk_insight(data)
            
            assert result == "High volatility detected. Increase safety stock by 20%."


def test_get_custom_ai_answer_with_successful_api():
    """Test custom Q&A returns AI answer when API works."""
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Yes, order 500 units for the next 2 weeks."
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_completion
            mock_groq_class.return_value = mock_client
            
            context = {
                'forecast': [100, 110],
                'product': {'name': 'Widget', 'sku': 'W001'},
                'scenario': 'Normal',
                'stock_data': {'recommended_stock': 500}
            }
            
            result = get_custom_ai_answer("How much should I order?", context)
            
            assert result == "Yes, order 500 units for the next 2 weeks."
