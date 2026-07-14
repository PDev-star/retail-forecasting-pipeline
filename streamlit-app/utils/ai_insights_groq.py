# AI-Powered Insights using Groq (BLAZING FAST!)
# RFP Requirement: AI explanations for demand scenarios
# Groq mentioned in RFP - ideal alternative to Gemini

import os
import sys
from groq import Groq
from typing import Dict, Any, Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Enhanced logging for debugging
if GROQ_API_KEY:
    masked = f"{GROQ_API_KEY[:7]}...{GROQ_API_KEY[-4:]}" if len(GROQ_API_KEY) > 11 else "***"
    print(f"🔑 Groq API Key configured: {masked}", flush=True)
    print(f"🚀 Using Groq inference (ultra-fast, RFP-approved)", flush=True)
    sys.stderr.write(f"DEBUG: Groq key length = {len(GROQ_API_KEY)}\n")
    sys.stderr.flush()
else:
    print("⚠️ No Groq API key configured", flush=True)
    sys.stderr.write("ERROR: GROQ_API_KEY environment variable is empty!\n")
    sys.stderr.flush()


def _call_groq(prompt: str) -> Optional[str]:
    """Call Groq API with enhanced error reporting"""
    if not GROQ_API_KEY:
        error_msg = "❌ No Groq API key configured!"
        print(error_msg, flush=True)
        sys.stderr.write(f"ERROR: {error_msg}\n")
        sys.stderr.flush()
        return None
    
    try:
        print(f"🌐 Calling Groq API (model: llama-3.3-70b-versatile)...", flush=True)
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful retail inventory analyst assistant. Provide concise, business-focused insights."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500,
            top_p=1,
            stream=False
        )
        result = chat_completion.choices[0].message.content
        print(f"✅ Groq API success (model: llama-3.3-70b-versatile)", flush=True)
        return result
    
    except Exception as e:
        error_details = f"⚠️ Groq API failed: {type(e).__name__}: {str(e)}"
        print(error_details, flush=True)
        sys.stderr.write(f"ERROR: {error_details}\n")
        sys.stderr.flush()
        
        # Check for specific error types
        error_str = str(e).lower()
        if "rate" in error_str or "429" in error_str:
            print("   → Rate limit hit (30 RPM)", flush=True)
        elif "quota" in error_str or "exceeded" in error_str:
            print("   → Daily quota exceeded (14,400 RPD)", flush=True)
        elif "401" in error_str or "unauthorized" in error_str:
            print("   → Invalid API key", flush=True)
        elif "403" in error_str or "forbidden" in error_str:
            print("   → Access denied", flush=True)
        
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
    
    response = _call_groq(prompt)
    
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
    
    response = _call_groq(prompt)
    
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
    
    response = _call_groq(prompt)
    
    if response:
        return response
    else:
        return f"""⚠️ **Risk Assessment:** Demand volatility is {volatility:.1f} units ({volatility_ratio:.1f}% of average), indicating {risk_level} risk. The {trend} trend adds uncertainty. **Mitigation:** {'Increase safety stock to handle demand spikes' if risk_level == 'HIGH' else 'Monitor closely for pattern changes'}."""


def get_custom_ai_answer(question: str, context: Dict[str, Any]) -> str:
    """Answer custom user question using Groq (META-PROMPTING)"""
    print(f"🤔 Custom Q&A called with question: {question[:50]}...", flush=True)
    
    if not GROQ_API_KEY:
        return """⚠️ **AI Service Unavailable**
        
No API key configured. Please add GROQ_API_KEY to environment variables.

**For Streamlit Cloud:**
1. Go to app settings → Secrets
2. Add: GROQ_API_KEY = "your-key-here"

**Get a free key:** https://console.groq.com/keys"""
    
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
    
    meta_prompt = f"""You are a retail inventory analyst AI assistant. A business user asked this question:

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

Keep it plain English, non-technical, business-focused. Under 120 words."""
    
    response = _call_groq(meta_prompt)
    
    if response:
        return response
    else:
        # Enhanced error message with actual error details
        key_status = f"Key present: {len(GROQ_API_KEY)} chars" if GROQ_API_KEY else "No key configured"
        return f"""⚠️ **AI Service Temporarily Unavailable**

Groq API encountered an error. This could be due to:
* Rate limits (30 requests per minute)
* Daily quota exceeded (14,400 requests per day)
* Temporary service issue
* Invalid API key

**Debug Info:**
* API Key Status: {key_status}

**Solutions:**
1. Wait a minute and try again
2. Check your Groq dashboard: https://console.groq.com
3. Verify API key is valid
4. Check Streamlit Cloud logs for detailed error

The fallback text-based insights are still available above."""
