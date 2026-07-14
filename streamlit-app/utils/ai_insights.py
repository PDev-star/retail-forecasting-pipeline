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
_available_model = None

# Discover available model at startup (minimal logging)
if GEMINI_API_KEYS:
    try:
        genai.configure(api_key=GEMINI_API_KEYS[0])
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'gemini-2.5' not in m.name.lower():
                available_models.append(m.name)
        
        if available_models:
            _available_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        else:
            _available_model = 'models/gemini-1.5-flash'
    except Exception:
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
    pct_change = ((forecast[-1] - forecast[0]) / forecast[0] * 100) if forecast[0] != 0 else 0
    
    prompt = f"""You are a retail inventory expert analyzing demand for {product['name']}.

**DATA:**
- Next {len(forecast)} days forecast: avg {avg_demand:.0f} units/day, ranging {min_demand:.0f}-{max_demand:.0f}
- Trend: {trend} ({pct_change:+.1f}% change)
- Context: {scenario}

**YOUR JOB:** Write a 3-sentence analysis that a procurement manager can ACT on immediately.

**RULES:**
- Sentence 1: Describe the demand pattern WITH SPECIFIC NUMBERS (don't just say "demand is decreasing")
- Sentence 2: Explain the business impact (revenue risk, inventory cost, or cash flow)
- Sentence 3: Give ONE specific action with a number (e.g., "reduce orders to 200 units" not "consider reducing")

**AVOID GENERIC PHRASES:**
❌ "may impact revenue"
❌ "consider adjusting"
❌ "plan inventory levels accordingly"

✅ Instead say: "Reduce next order to 150 units" or "Increase safety stock by 30%"

Keep under 80 words. Be direct and specific."""
    
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
    
    coverage_days = recommended_stock / (reorder_point / lead_time_days) if reorder_point > 0 else 0
    safety_pct = (safety_stock / recommended_stock * 100) if recommended_stock > 0 else 0
    
    prompt = f"""You are a retail inventory expert. Explain this stock recommendation to a buyer who needs to make a purchase decision TODAY.

**THE NUMBERS:**
- Order quantity: {recommended_stock} units
- Reorder trigger: {reorder_point} units (when stock falls below this)
- Safety buffer: {safety_stock} units ({safety_pct:.0f}% of order)
- Lead time: {lead_time_days} days

**YOUR JOB:** Write 2-3 sentences that help the buyer understand if this is the RIGHT amount to order.

**STRUCTURE:**
1. Explain why this order size makes sense (mention coverage or runway)
2. State the risk level (LOW/MEDIUM/HIGH) with a reason
3. Tell them the ONE thing to watch or do next

**EXAMPLES OF GOOD INSIGHTS:**
✅ "This order covers {coverage_days:.0f} days of demand. Risk is LOW because..."
✅ "With {lead_time_days} days lead time, you'll need to reorder when you have..."

**AVOID:**
❌ "This order quantity balances stock needs"
❌ "The buyer should reorder when stock falls"

Be specific with numbers. Under 70 words."""
    
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
    
    prompt = f"""You are a retail supply chain risk expert. A procurement manager needs to understand the RISK in this forecast.

**THE SITUATION:**
- Demand swings: {min(volatility, 999):.0f} units between peak and low ({volatility_ratio:.0f}% volatility)
- Average: {avg_demand:.0f} units/day
- Trend: {trend}
- Context: {scenario}
- Risk level: {risk_level}

**YOUR JOB:** Write 2-3 sentences that help them avoid stockouts OR overstocking.

**STRUCTURE:**
1. State the risk level and WHY it's that level (be specific about what creates the risk)
2. What COULD GO WRONG (stockout? excess inventory? cash tied up?)
3. ONE concrete mitigation action (with a number if possible)

**EXAMPLES:**
✅ "Risk level is HIGH due to {volatility_ratio:.0f}% swings. Overstocking could tie up $XX in inventory..."
✅ "Risk is MEDIUM. The {trend} trend means you might face stockouts by day X..."

**AVOID:**
❌ "Demand volatility adds uncertainty"
❌ "Consider implementing flexible inventory management"

Be direct about what could go wrong. Under 70 words."""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        return f"""⚠️ **Risk Assessment:** Demand volatility is {volatility:.1f} units ({volatility_ratio:.1f}% of average), indicating {risk_level} risk. The {trend} trend adds uncertainty. **Mitigation:** {'Increase safety stock to handle demand spikes' if risk_level == 'HIGH' else 'Monitor closely for pattern changes'}."""


def get_custom_ai_answer(question: str, context: Dict[str, Any]) -> str:
    """Answer custom user question using Gemini (META-PROMPTING)"""
    if not GEMINI_API_KEYS:
        return """⚠️ **AI Service Unavailable**
        
No API keys configured. Please add GEMINI_API_KEY to environment variables.

**For Streamlit Cloud:**
1. Go to app settings → Secrets
2. Add: `GEMINI_API_KEY = "your-key-here"`
3. Optionally add GEMINI_API_KEY_2 and GEMINI_API_KEY_3 for backup"""
    
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
    
    meta_prompt = f"""You are a retail inventory analyst AI assistant. A buyer asked:

"{question}"

**FORECAST DATA:**
- Product: {product.get('name', 'Unknown')} (SKU: {product.get('sku', 'N/A')})
- Next {len(forecast)} days demand: {forecast[:7] if forecast else 'N/A'}
- Average: {avg_demand:.0f} units/day
- Trend: {trend}
- Scenario: {scenario}
- Recommended order: {stock_data.get('recommended_stock', 'N/A')} units
- Safety buffer: {stock_data.get('safety_stock', 'N/A')} units

**YOUR JOB:** Answer their question in 2-3 sentences with SPECIFIC recommendations.

**STRUCTURE:**
1. Direct answer (with numbers)
2. Business impact (money/risk/timeline)
3. ONE action to take

**RULES:**
- Be specific (use the actual numbers from the data)
- Avoid vague phrases like "you may want to consider"
- Give concrete actions like "Order 200 units by Friday"

Under 100 words, plain English."""
    
    response = _call_gemini_with_fallback(meta_prompt)
    
    if response:
        return response
    else:
        return f"""⚠️ **AI Service Temporarily Unavailable**

All {len(GEMINI_API_KEYS)} API keys have hit rate limits or encountered errors.

**Common Issues:**
* Rate limits: 15 requests per minute per key (varies by model)
* Daily limit: 1,500 requests per day per key
* Blocked project: One key may have 403 error

**Solutions:**
1. Wait a few minutes and try again (rate limits reset)
2. Generate fresh API keys at: https://aistudio.google.com/apikey
3. Use DIFFERENT Google accounts for each key (keys from same account share quota)"""
