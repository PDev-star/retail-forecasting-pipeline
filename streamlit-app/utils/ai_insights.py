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
                # Skip deprecated gemini-2.5-* models (404 errors for new users)
                if 'gemini-2.5' in m.name.lower():
                    print(f"  ⏭️  {m.name} (skipped - deprecated)")
                    continue
                available_models.append(m.name)
                print(f"  ✅ {m.name}")
        
        if available_models:
            # Prefer gemini-1.5-flash specifically (most stable)
            if 'models/gemini-1.5-flash' in available_models:
                _available_model = 'models/gemini-1.5-flash'
                print(f"\n🎯 Selected model: {_available_model} (preferred stable model)")
            else:
                # Otherwise pick first available flash model
                flash_models = [m for m in available_models if 'flash' in m.lower() and '1.5' in m]
                _available_model = flash_models[0] if flash_models else available_models[0]
                print(f"\n🎯 Selected model: {_available_model}")
        else:
            print("  ⚠️ No models found - will try fallback")
            _available_model = 'models/gemini-1.5-flash'  # Fallback to most stable
    
    except Exception as e:
        print(f"  ⚠️ Could not list models: {e}")
        print(f"  → Using fallback: models/gemini-1.5-flash")
        _available_model = 'models/gemini-1.5-flash'
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
    
    # Fix trend calculation: handle equal values as "stable"
    if len(forecast) == 1:
        trend = "stable"
    elif forecast[-1] > forecast[0]:
        trend = "increasing"
    elif forecast[-1] < forecast[0]:
        trend = "decreasing"
    else:  # forecast[-1] == forecast[0]
        trend = "stable"
    
    max_demand = max(forecast)
    min_demand = min(forecast)
    
    # Calculate percentage change for more specific insights
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
    
    # Calculate useful ratios
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
    
    # Fix trend calculation: handle equal values as "stable" (same as get_forecast_insight)
    if not forecast:
        trend = "unknown"
    elif len(forecast) == 1:
        trend = "stable"
    elif forecast[-1] > forecast[0]:
        trend = "increasing"
    elif forecast[-1] < forecast[0]:
        trend = "decreasing"
    else:  # forecast[-1] == forecast[0]
        trend = "stable"
    
    # META-PROMPT: Let Gemini understand the question and frame its own answer
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
3. Use DIFFERENT Google accounts for each key (keys from same account share quota)

**Debug Info:**
* Keys configured: {len(GEMINI_API_KEYS)}
* Current model: {_available_model or 'Not discovered'}"""
