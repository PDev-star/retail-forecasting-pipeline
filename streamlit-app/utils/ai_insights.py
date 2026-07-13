# AI-Powered Insights using Gemini (Dynamic Model Selection)
# RFP Requirement: AI explanations for demand scenarios

import os
import google.generativeai as genai
from typing import Dict, Any, Optional

# ============================================================================
# MULTI-KEY ROTATION FOR QUOTA PROTECTION
# ============================================================================
# Free tier: 15 RPM, 1,500 RPD per key (varies by model)
# Multiple keys ensure demo works even if one hits quota

GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY", ""),       # Primary key
    os.getenv("GEMINI_API_KEY_2", ""),     # Backup key 1
    os.getenv("GEMINI_API_KEY_3", ""),     # Backup key 2
]

# Filter out empty keys
GEMINI_API_KEYS = [k for k in GEMINI_API_KEYS if k.strip()]

_current_key_index = 0
_available_model = None  # Cache the working model

# ============================================================================
# DEBUGGING: Log key availability and discover models at startup
# ============================================================================
print(f"🔑 Gemini API Keys configured: {len(GEMINI_API_KEYS)}")
for i, key in enumerate(GEMINI_API_KEYS):
    masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
    print(f"  Key #{i+1}: {masked}")

# DISCOVER AVAILABLE MODELS (like notebook does)
if GEMINI_API_KEYS:
    print("\n📋 Discovering available Gemini models...")
    try:
        genai.configure(api_key=GEMINI_API_KEYS[0])
        
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                print(f"  ✅ {m.name}")
        
        if available_models:
            # Pick first available model (prefer flash over pro for speed)
            flash_models = [m for m in available_models if 'flash' in m.lower()]
            _available_model = flash_models[0] if flash_models else available_models[0]
            print(f"\n🎯 Selected model: {_available_model}")
        else:
            print("  ⚠️ No models found - will try fallback")
            _available_model = 'gemini-1.5-flash'  # Fallback
    
    except Exception as e:
        print(f"  ⚠️ Could not list models: {e}")
        print(f"  → Using fallback: gemini-1.5-flash")
        _available_model = 'gemini-1.5-flash'
else:
    print("⚠️ No API keys configured")


def _get_next_api_key() -> Optional[str]:
    """Get next available API key (rotates through keys on failure)"""
    global _current_key_index
    
    if not GEMINI_API_KEYS:
        return None
    
    # Try current key
    key = GEMINI_API_KEYS[_current_key_index]
    
    # Rotate to next key for next call (round-robin)
    _current_key_index = (_current_key_index + 1) % len(GEMINI_API_KEYS)
    
    return key


def _call_gemini_with_fallback(prompt: str, max_retries: int = 3) -> Optional[str]:
    """
    Call Gemini API with automatic key rotation on failure
    
    Args:
        prompt: The prompt to send to Gemini
        max_retries: Number of keys to try before giving up
    
    Returns:
        AI response text, or None if all keys fail
    """
    if not GEMINI_API_KEYS:
        print("❌ No API keys configured!")
        return None
    
    if not _available_model:
        print("❌ No model available!")
        return None
    
    attempts = min(max_retries, len(GEMINI_API_KEYS))
    last_error = None
    
    for attempt in range(attempts):
        # Store index BEFORE getting key (for accurate logging)
        key_index = _current_key_index
        api_key = _get_next_api_key()
        
        if not api_key:
            continue
        
        try:
            genai.configure(api_key=api_key)
            # Use the model we discovered at startup (like notebook does)
            model = genai.GenerativeModel(_available_model)
            response = model.generate_content(prompt)
            
            # Success!
            print(f"✅ Gemini API success (key #{key_index + 1}, model: {_available_model})")
            return response.text
        
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ Gemini API failed with key #{key_index + 1}: {e}")
            
            # Check if it's a rate limit error
            error_str = str(e).lower()
            if "quota" in error_str or "rate limit" in error_str or "429" in error_str:
                print(f"   → Rate limit hit on key #{key_index + 1}")
            elif "api_key" in error_str or "invalid" in error_str or "401" in error_str:
                print(f"   → Invalid API key #{key_index + 1}")
            elif "403" in error_str or "denied access" in error_str:
                print(f"   → Access denied for key #{key_index + 1} (project blocked)")
            elif "404" in error_str or "not found" in error_str:
                print(f"   → Model not found - may need to update model name")
            
            # Try next key
            continue
    
    # All keys failed - log details
    print(f"❌ All {len(GEMINI_API_KEYS)} API keys exhausted")
    print(f"   Last error: {last_error}")
    return None


# ============================================================================
# PRE-BUILT AI INSIGHTS (3 SCENARIOS - RFP REQUIREMENT)
# ============================================================================

def get_forecast_insight(data: Dict[str, Any]) -> str:
    """
    Generate AI insight for forecast analysis
    
    Args:
        data: dict with keys: forecast, product, scenario
    
    Returns:
        AI-generated forecast insight (plain English)
    """
    forecast = data['forecast']
    product = data['product']
    scenario = data.get('scenario', 'Normal conditions')
    
    # Handle edge case: empty forecast
    if not forecast:
        return """📊 **Forecast Summary:** No forecast data available. Please generate a forecast first to see AI insights."""
    
    avg_demand = sum(forecast) / len(forecast)
    trend = "increasing" if len(forecast) > 1 and forecast[-1] > forecast[0] else "stable" if len(forecast) == 1 else "decreasing"
    max_demand = max(forecast)
    min_demand = min(forecast)
    
    prompt = f"""
You are a retail inventory analyst. Explain this demand forecast in plain English for a procurement manager:

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

Keep it under 100 words, plain English, business-focused.
"""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        # Fallback if all API keys fail
        return f"""📊 **Forecast Summary:** Average daily demand is {avg_demand:.1f} units over the next {len(forecast)} days, showing a {trend} trend. Demand ranges from {min_demand:.1f} to {max_demand:.1f} units. **Recommendation:** Plan inventory levels accordingly, considering the {trend} trend in your reorder calculations."""


def get_stock_insight(data: Dict[str, Any]) -> str:
    """
    Generate AI insight for stock recommendations
    
    Args:
        data: dict with keys: recommended_stock, reorder_point, safety_stock, lead_time_days
    
    Returns:
        AI-generated stock recommendation insight
    """
    recommended_stock = data['recommended_stock']
    reorder_point = data['reorder_point']
    safety_stock = data['safety_stock']
    lead_time_days = data['lead_time_days']
    
    prompt = f"""
You are a retail inventory analyst. Explain this stock recommendation in plain English:

Recommended order quantity: {recommended_stock} units
Reorder point: {reorder_point} units (trigger reorder when stock falls to this level)
Safety stock buffer: {safety_stock} units
Supplier lead time: {lead_time_days} days

In 2-3 sentences, explain:
1. Why this order quantity makes sense?
2. What's the risk level (low/medium/high)?
3. One action the buyer should take?

Keep it under 80 words, non-technical language.
"""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        # Fallback
        return f"""🎯 **Stock Recommendation:** Order {recommended_stock} units to cover {lead_time_days} days of demand plus a {safety_stock}-unit safety buffer. Set your reorder point at {reorder_point} units to avoid stockouts. This provides adequate protection against demand spikes."""


def get_risk_insight(data: Dict[str, Any]) -> str:
    """
    Generate AI insight for risk assessment
    
    Args:
        data: dict with keys: volatility, avg_demand, trend, scenario
    
    Returns:
        AI-generated risk assessment
    """
    volatility = data['volatility']
    avg_demand = data['avg_demand']
    trend = data['trend']
    scenario = data.get('scenario', 'Normal conditions')
    
    volatility_ratio = (volatility / avg_demand * 100) if avg_demand > 0 else 0
    risk_level = "HIGH" if volatility_ratio > 50 else "MEDIUM" if volatility_ratio > 25 else "LOW"
    
    prompt = f"""
You are a retail risk analyst. Assess this forecast risk:

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

Keep it under 80 words, focus on business risk.
"""
    
    response = _call_gemini_with_fallback(prompt)
    
    if response:
        return response
    else:
        # Fallback
        return f"""⚠️ **Risk Assessment:** Demand volatility is {volatility:.1f} units ({volatility_ratio:.1f}% of average), indicating {risk_level} risk. The {trend} trend adds uncertainty. **Mitigation:** {'Increase safety stock to handle demand spikes' if risk_level == 'HIGH' else 'Monitor closely for pattern changes'}."""


# ============================================================================
# CUSTOM Q&A (ADVANCED FEATURE - GOES BEYOND RFP)
# ============================================================================

def get_custom_ai_answer(question: str, context: Dict[str, Any]) -> str:
    """
    Answer custom user question using Gemini (META-PROMPTING)
    
    This is the advanced feature: Gemini creates its own system prompt
    based on the user's question, then answers it!
    
    Args:
        question: User's custom question (str)
        context: Dict with forecast, product, stock_data, scenario
    
    Returns:
        AI-generated answer (plain English)
    """
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
    trend = "increasing" if forecast and len(forecast) > 1 and forecast[-1] > forecast[0] else "stable" if len(forecast) == 1 else "decreasing"
    
    # META-PROMPT: Let Gemini understand the question and frame its own answer
    meta_prompt = f"""
You are a retail inventory analyst AI assistant. A business user asked this question:

"{question}"

Here is the forecast data context:
- Product: {product.get('name', 'Unknown')} (SKU: {product.get('sku', 'N/A')})
- Forecast horizon: {len(forecast)} days
- Predicted demand (next 7 days): {forecast[:7] if forecast else 'N/A'}
- Average daily demand: {avg_demand:.1f} units
- Demand trend: {trend}
- Scenario: {scenario}
- Recommended stock level: {stock_data.get('recommended_stock', 'N/A')} units
- Safety stock: {stock_data.get('safety_stock', 'N/A')} units

Answer the user's question in 2-4 sentences, focusing on:
1. Direct answer to their question
2. Business impact (revenue, cost, or operational risk)
3. One actionable recommendation

Keep it plain English, non-technical, business-focused. Under 120 words.
"""
    
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
3. Use DIFFERENT Google accounts for each key (keys from same account share quota)

**Debug Info:**
* Keys configured: {len(GEMINI_API_KEYS)}
* Current model: {_available_model or 'Not discovered'}"""
