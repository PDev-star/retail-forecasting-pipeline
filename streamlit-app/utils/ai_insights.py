# AI-Powered Insights using Gemini (Dynamic Model Selection)
# RFP Requirement: AI explanations for demand scenarios

import os
import google.generativeai as genai
from typing import Dict, Any, Optional

# Multi-key rotation for quota protection
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY", ""),
    os.getenv("GEMINI_API_KEY_2", ""),
    os.getenv("GEMINI_API_KEY_3", ""),
]

GEMINI_API_KEYS = [k for k in GEMINI_API_KEYS if k.strip()]

_current_key_index = 0
_available_model = 'models/gemini-1.5-flash'


def _get_next_api_key() -> Optional[str]:
    """Get next available API key (rotates through keys on failure)"""
    global _current_key_index
    
    if not GEMINI_API_KEYS:
        return None
    
    key = GEMINI_API_KEYS[_current_key_index]
    _current_key_index = (_current_key_index + 1) % len(GEMINI_API_KEYS)
    
    return key


def _call_gemini_with_fallback(prompt: str, max_retries: int = 3) -> Optional[str]:
    """Call Gemini API with automatic key rotation on failure"""
    if not GEMINI_API_KEYS or not _available_model:
        return None
    
    attempts = min(max_retries, len(GEMINI_API_KEYS))
    
    for _ in range(attempts):
        api_key = _get_next_api_key()
        if not api_key:
            continue
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(_available_model)
            response = model.generate_content(prompt)
            return response.text
        
        except Exception:
            continue
    
    return None


def get_forecast_insight(data: Dict[str, Any]) -> str:
    """Generate AI insight for forecast analysis"""
    forecast = data['forecast']
    product = data['product']
    scenario = data.get('scenario', 'Normal conditions')
    
    if not forecast:
        return """📊 **Forecast Summary:** No forecast data available. Please generate a forecast first to see AI insights."""
    
    avg_demand = sum(forecast) / len(forecast)
    
    if len(forecast) == 1:
        trend = "stable"
    elif forecast[-1] > forecast[0]:
        trend = "increasing"
    elif forecast[-1] < forecast[0]:
        trend = "decreasing"
    else:
        trend = "stable"
    
    max_demand = max(forecast)
    min_demand = min(forecast)
    
    prompt = f"""You are a retail inventory analyst. Explain this demand forecast in plain English for a procurement manager:

Product: {product['name']} (SKU: {product['sku']})
Forecast period: {len(forecast)} days
Average daily demand: {avg_demand:.1f} units
Demand range: {min_demand:.1f} to {max_demand:.1f} units
Trend: {trend}
Scenario: {scenario}

Provide a 3-sentence summary:
1. What's the demand pattern?
2. Business implication (revenue/cost impact)?
3. One actionable recommendation?

Keep it under 100 words, plain English, business-focused."""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        return f"""📊 **Forecast Summary:** Average daily demand is {avg_demand:.1f} units over the next {len(forecast)} days, showing a {trend} trend. Demand ranges from {min_demand:.1f} to {max_demand:.1f} units. **Recommendation:** Plan inventory levels accordingly, considering the {trend} trend in your reorder calculations."""


def get_stock_insight(data: Dict[str, Any]) -> str:
    """Generate AI insight for stock recommendations"""
    recommended_stock = data['recommended_stock']
    reorder_point = data['reorder_point']
    safety_stock = data['safety_stock']
    lead_time_days = data['lead_time_days']
    
    prompt = f"""You are a retail inventory analyst. Explain this stock recommendation in plain English:

Recommended order quantity: {recommended_stock} units
Reorder point: {reorder_point} units (trigger reorder when stock falls to this level)
Safety stock buffer: {safety_stock} units
Supplier lead time: {lead_time_days} days

In 2-3 sentences, explain:
1. Why this order quantity makes sense?
2. What's the risk level (low/medium/high)?
3. One action the buyer should take?

Keep it under 80 words, non-technical language."""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        return f"""🎯 **Stock Recommendation:** Order {recommended_stock} units to cover {lead_time_days} days of demand plus a {safety_stock}-unit safety buffer. Set your reorder point at {reorder_point} units to avoid stockouts. This provides adequate protection against demand spikes."""


def get_risk_insight(data: Dict[str, Any]) -> str:
    """Generate AI insight for risk assessment"""
    volatility = data['volatility']
    avg_demand = data['avg_demand']
    trend = data['trend']
    scenario = data.get('scenario', 'Normal conditions')
    
    volatility_ratio = (volatility / avg_demand * 100) if avg_demand > 0 else 0
    risk_level = "HIGH" if volatility_ratio > 50 else "MEDIUM" if volatility_ratio > 25 else "LOW"
    
    prompt = f"""You are a retail risk analyst. Assess this forecast risk:

Demand volatility: {volatility:.1f} units (difference between peak and minimum)
Average daily demand: {avg_demand:.1f} units
Volatility ratio: {volatility_ratio:.1f}%
Demand trend: {trend}
Scenario: {scenario}
Risk level: {risk_level}

In 2-3 sentences:
1. What's the risk level and why?
2. What could go wrong?
3. One mitigation action?

Keep it under 80 words, focus on business risk."""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        return f"""⚠️ **Risk Assessment:** Demand volatility is {volatility:.1f} units ({volatility_ratio:.1f}% of average), indicating {risk_level} risk. The {trend} trend adds uncertainty. **Mitigation:** {'Increase safety stock to handle demand spikes' if risk_level == 'HIGH' else 'Monitor closely for pattern changes'}."""


def get_custom_ai_answer(question: str, context: Dict[str, Any]) -> str:
    """Answer custom user question using Gemini (META-PROMPTING)"""
    if not GEMINI_API_KEYS:
        return """⚠️ **AI Service Unavailable**
        
No API keys configured. Please add GEMINI_API_KEY to environment variables."""
    
    forecast = context.get('forecast', [])
    product = context.get('product', {})
    scenario = context.get('scenario', 'Normal conditions')
    stock_data = context.get('stock_data', {})
    
    avg_demand = sum(forecast) / len(forecast) if forecast else 0
    
    if not forecast:
        trend = "unknown"
    elif len(forecast) == 1:
        trend = "stable"
    elif forecast[-1] > forecast[0]:
        trend = "increasing"
    elif forecast[-1] < forecast[0]:
        trend = "decreasing"
    else:
        trend = "stable"
    
    prompt = f"""You are a retail inventory analyst AI assistant. A buyer asked:

"{question}"

FORECAST DATA:
- Product: {product.get('name', 'Unknown')} (SKU: {product.get('sku', 'N/A')})
- Next {len(forecast)} days demand: {forecast[:7] if forecast else 'N/A'}
- Average: {avg_demand:.0f} units/day
- Trend: {trend}
- Scenario: {scenario}
- Recommended order: {stock_data.get('recommended_stock', 'N/A')} units
- Safety buffer: {stock_data.get('safety_stock', 'N/A')} units

Answer their question in 2-3 sentences. Be specific and actionable.

Keep under 100 words, plain English."""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        return """⚠️ **AI Service Temporarily Unavailable**

All API keys have hit rate limits. Please try again in a few minutes."""
