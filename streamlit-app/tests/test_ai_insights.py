"""
Unit tests for AI Insights module (utils/ai_insights.py)
Tests all AI-powered functions: forecast, stock, risk, and custom Q&A
"""

import pytest
from unittest.mock import patch, MagicMock
from utils import ai_insights
from utils.ai_insights import (
    get_forecast_insight,
    get_stock_insight,
    get_risk_insight,
    get_custom_ai_answer,
    _call_gemini_with_fallback,
    _get_next_api_key
)


# ============================================================================
# TEST GROUP 1: FALLBACK TESTS (No API keys needed!)
# ============================================================================

def test_forecast_insight_fallback():
    """When API unavailable, get_forecast_insight returns text fallback."""
    
    # Clear API keys to force fallback
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
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
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
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
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        data = {
            'volatility': 50,
            'avg_demand': 100,
            'trend': 'increasing',
            'scenario': 'Normal'
        }
        
        result = get_risk_insight(data)
        
        assert "Risk Assessment" in result or "volatility" in result.lower()
        assert "50.0%" in result  # Volatility ratio


def test_custom_ai_answer_no_keys():
    """When no API keys configured, custom Q&A returns helpful error message."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        context = {
            'forecast': [100, 105],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal',
            'stock_data': {'recommended_stock': 500}
        }
        
        result = get_custom_ai_answer("How much should I order?", context)
        
        assert "unavailable" in result.lower() or "api key" in result.lower()
        assert "GEMINI_API_KEY" in result


# ============================================================================
# TEST GROUP 2: EDGE CASES (Unusual inputs)
# ============================================================================

def test_insights_with_empty_forecast():
    """AI insights handle empty forecast gracefully."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        data = {
            'forecast': [],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "no forecast" in result.lower() or "unavailable" in result.lower()


def test_insights_with_single_value_forecast():
    """AI insights handle single-value forecast."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        data = {
            'forecast': [100],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "100.0" in result  # Average demand
        assert "stable" in result.lower()  # Single value = stable trend


# ============================================================================
# TEST GROUP 3: KEY ROTATION TESTS (Multi-key logic)
# ============================================================================

def test_get_next_api_key_rotation():
    """API key rotation cycles through all keys."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['key1', 'key2', 'key3']):
        # Reset index
        ai_insights._current_key_index = 0
        
        key1 = _get_next_api_key()
        key2 = _get_next_api_key()
        key3 = _get_next_api_key()
        key4 = _get_next_api_key()  # Should cycle back to key1
        
        assert key1 == 'key1'
        assert key2 == 'key2'
        assert key3 == 'key3'
        assert key4 == 'key1'


def test_get_next_api_key_no_keys():
    """When no keys configured, _get_next_api_key returns None."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        key = _get_next_api_key()
        assert key is None


def test_get_next_api_key_single_key():
    """Single key keeps returning the same key."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['only_key']):
        ai_insights._current_key_index = 0
        
        key1 = _get_next_api_key()
        key2 = _get_next_api_key()
        key3 = _get_next_api_key()
        
        assert key1 == 'only_key'
        assert key2 == 'only_key'
        assert key3 == 'only_key'


# ============================================================================
# TEST GROUP 4: GEMINI API MOCK TESTS (Simulated API calls)
# ============================================================================

def test_call_gemini_success_first_try():
    """Test Gemini API succeeds on first key."""
    mock_response = MagicMock()
    mock_response.text = "AI-generated insight about demand patterns."
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['test_key']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure') as mock_configure:
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    result = _call_gemini_with_fallback("Test prompt")
                    
                    assert result == "AI-generated insight about demand patterns."
                    mock_configure.assert_called_once()
                    mock_model.generate_content.assert_called_once_with("Test prompt")


def test_call_gemini_success_after_retry():
    """Test Gemini API succeeds on second key after first fails."""
    mock_response = MagicMock()
    mock_response.text = "Success on second key!"
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['bad_key', 'good_key']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure') as mock_configure:
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    
                    # First call fails, second succeeds
                    mock_model.generate_content.side_effect = [
                        Exception("Quota exceeded"),
                        mock_response
                    ]
                    mock_model_class.return_value = mock_model
                    
                    result = _call_gemini_with_fallback("Test prompt", max_retries=2)
                    
                    assert result == "Success on second key!"
                    assert mock_configure.call_count == 2


def test_call_gemini_all_keys_fail():
    """Test Gemini API returns None when all keys fail."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['key1', 'key2']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model.generate_content.side_effect = Exception("Rate limit exceeded")
                    mock_model_class.return_value = mock_model
                    
                    result = _call_gemini_with_fallback("Test prompt", max_retries=2)
                    
                    assert result is None


# ============================================================================
# TEST GROUP 5: FULL INSIGHT FUNCTION TESTS (With mocked API)
# ============================================================================

def test_get_forecast_insight_with_successful_api():
    """Test get_forecast_insight returns AI-generated text when API works."""
    mock_response = MagicMock()
    mock_response.text = "Your demand is trending upward. Stock up now!"
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['test_key']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    data = {
                        'forecast': [100, 110, 120],
                        'product': {'name': 'Widget', 'sku': 'W001'},
                        'scenario': 'Normal'
                    }
                    
                    result = get_forecast_insight(data)
                    
                    assert result == "Your demand is trending upward. Stock up now!"


def test_get_forecast_insight_with_failed_api():
    """Test get_forecast_insight returns fallback when API fails."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['bad_key']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model.generate_content.side_effect = Exception("API Error")
                    mock_model_class.return_value = mock_model
                    
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
    mock_response = MagicMock()
    mock_response.text = "This order size ensures 5 days of buffer stock."
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['test_key']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
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
    mock_response = MagicMock()
    mock_response.text = "High volatility detected. Increase safety stock by 20%."
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['test_key']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
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
    mock_response = MagicMock()
    mock_response.text = "Yes, order 500 units for the next 2 weeks."
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', ['test_key']):
        with patch.object(ai_insights, '_available_model', 'gemini-1.5-flash'):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    context = {
                        'forecast': [100, 105],
                        'product': {'name': 'Widget', 'sku': 'W001'},
                        'scenario': 'Normal',
                        'stock_data': {'recommended_stock': 500}
                    }
                    
                    result = get_custom_ai_answer("How much should I order?", context)
                    
                    assert result == "Yes, order 500 units for the next 2 weeks."


def test_get_custom_ai_answer_no_keys_configured():
    """Test custom Q&A returns error message when no keys."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        context = {
            'forecast': [100, 105],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal',
            'stock_data': {}
        }
        
        result = get_custom_ai_answer("How much?", context)
        
        assert "unavailable" in result.lower()
        assert "GEMINI_API_KEY" in result


# ============================================================================
# TEST GROUP 6: DATA VALIDATION TESTS (Extreme inputs)
# ============================================================================

def test_forecast_insight_with_zero_avg_demand():
    """Test forecast insight handles zero average demand."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        data = {
            'forecast': [0, 0, 0],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        assert "0.0" in result  # Zero average
        assert "stable" in result.lower()


def test_risk_insight_with_zero_avg_demand():
    """Test risk insight handles zero average demand (avoid division by zero)."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        data = {
            'volatility': 10,
            'avg_demand': 0,  # Zero average
            'trend': 'stable',
            'scenario': 'Normal'
        }
        
        result = get_risk_insight(data)
        
        # Should not crash, should handle gracefully
        assert "Risk Assessment" in result or "volatility" in result.lower()


def test_custom_ai_answer_with_empty_context():
    """Test custom Q&A with minimal context data."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        context = {
            'forecast': [],
            'product': {},
            'scenario': '',
            'stock_data': {}
        }
        
        result = get_custom_ai_answer("Test question?", context)
        
        # Should return error message or fallback
        assert len(result) > 0
        assert "unavailable" in result.lower() or "api" in result.lower()


def test_insights_with_very_large_forecast():
    """Test insights handle large forecast arrays."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        data = {
            'forecast': [100 + i for i in range(1000)],  # 1000 days
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Normal'
        }
        
        result = get_forecast_insight(data)
        
        # Should compute avg correctly
        expected_avg = sum(data['forecast']) / len(data['forecast'])
        assert f"{expected_avg:.1f}" in result


def test_insights_with_negative_values():
    """Test insights handle negative forecast values (returns, refunds)."""
    
    with patch.object(ai_insights, 'GEMINI_API_KEYS', []):
        data = {
            'forecast': [-50, -20, 10, 30],
            'product': {'name': 'Widget', 'sku': 'W001'},
            'scenario': 'Returns spike'
        }
        
        result = get_forecast_insight(data)
        
        # Should still compute insights
        avg = sum(data['forecast']) / len(data['forecast'])
        assert f"{avg:.1f}" in result or "demand" in result.lower()
