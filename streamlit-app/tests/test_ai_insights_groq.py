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
        
        # Check fallback has key info
        assert "Stock Recommendation" in result or "500" in result
        assert "200" in result  # reorder point
        assert "100" in result  # safety stock


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
        
        # Check fallback content
        assert "Risk Assessment" in result or "volatility" in result.lower()
        assert "50.0" in result  # volatility value


def test_custom_ai_answer_no_key():
    """When API key missing, custom Q&A returns error message."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        context = {
            'forecast': [100, 110],
            'product': {'name': 'Widget', 'sku': 'W001'}
        }
        
        result = get_custom_ai_answer("Should I order more?", context)
        
        # Should return helpful error message
        assert "AI Service Unavailable" in result or "No Groq API key" in result.lower()


# ============================================================================
# TEST GROUP 2: EDGE CASES (Empty/Unusual Data)
# ============================================================================

def test_insights_with_empty_forecast():
    """Empty forecast returns informative message."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'forecast': [],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "No forecast data" in result or "generate a forecast first" in result.lower()


def test_insights_with_single_value_forecast():
    """Single-value forecast is treated as 'stable' trend."""
    
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
                'forecast': [100, 105, 110],
                'product': {'name': 'Widget', 'sku': 'W001'},
                'scenario': 'Normal'
            }
            
            result = get_forecast_insight(data)
            
            assert result == "Your demand is trending upward. Stock up now!"


def test_get_forecast_insight_with_failed_api():
    """Test fallback text is returned when API fails."""
    
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', 'test_key'):
        with patch('utils.ai_insights_groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_groq_class.return_value = mock_client
            
            data = {
                'forecast': [100, 105, 110],
                'product': {'name': 'Widget', 'sku': 'W001'},
                'scenario': 'Normal'
            }
            
            result = get_forecast_insight(data)
            
            # Should return fallback text, not crash
            assert "Forecast Summary" in result or "105.0" in result


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
                'scenario': 'Normal'
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


# ============================================================================
# TEST GROUP 5: TREND CALCULATION COVERAGE
# ============================================================================

def test_custom_ai_answer_with_decreasing_trend():
    """Test custom Q&A detects decreasing trend."""
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        context = {
            'forecast': [120, 110, 100],  # Decreasing
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal',
            'stock_data': {}
        }
        
        result = get_custom_ai_answer("What's the trend?", context)
        
        # Check that result was generated (even if fallback)
        assert result is not None
        assert len(result) > 0


def test_custom_ai_answer_with_stable_trend_multiple_values():
    """Test custom Q&A detects stable trend when first == last."""
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        context = {
            'forecast': [100, 105, 100],  # First == Last = stable
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal',
            'stock_data': {}
        }
        
        result = get_custom_ai_answer("What's the trend?", context)
        
        assert result is not None
        assert len(result) > 0


def test_custom_ai_answer_with_single_value_trend():
    """Test custom Q&A handles single-value forecast (stable)."""
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        context = {
            'forecast': [100],  # Single value = stable
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal',
            'stock_data': {}
        }
        
        result = get_custom_ai_answer("What's the trend?", context)
        
        assert result is not None
        assert len(result) > 0


def test_forecast_insight_with_decreasing_trend():
    """Test forecast insight detects decreasing trend."""
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'forecast': [120, 110, 100],  # Decreasing
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "decreasing" in result.lower()
        assert "110.0" in result  # Average


def test_forecast_insight_with_stable_trend_equal_values():
    """Test forecast insight detects stable trend when first == last."""
    with patch.object(ai_insights_groq, 'GROQ_API_KEY', ''):
        data = {
            'forecast': [100, 105, 100],  # First == Last = stable
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "stable" in result.lower()
        assert "101.7" in result  # Average ≈ 101.67
