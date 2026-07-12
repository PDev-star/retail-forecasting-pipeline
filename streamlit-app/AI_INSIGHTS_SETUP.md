# AI Insights Setup Guide

## Overview

The Streamlit app uses **Gemini 2.5 Flash** to generate real AI-powered insights in plain English.

**RFP Requirement:** "Gemini/Groq AI-powered explanations for 3+ demand scenarios"

## Features

1. **Pre-built AI Insights (3 scenarios):**
   - 📊 Forecast Analysis
   - 🎯 Stock Recommendations  
   - ⚠️ Risk Assessment

2. **Custom Q&A (Advanced Feature - Goes Beyond RFP!):**
   - Users can ask ANY question about the forecast
   - Gemini dynamically creates the prompt and answers
   - Examples: "Should I increase orders?", "What if demand drops 30%?"

## Multi-Key Rotation for Quota Protection

**Problem:** Gemini free tier limits:
- 15 requests/minute per key
- 1,500 requests/day per key

**Solution:** Use 2-3 API keys with automatic rotation!

If Key 1 hits quota → automatically tries Key 2 → tries Key 3 → fallback to text

## Setup Instructions

### Step 1: Get Free Gemini API Keys (5 min)

1. Go to: https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API key in new project"**
4. Copy the key (it starts with `AIza...`)
5. Repeat for 2-3 keys (use different Google accounts or create multiple keys)

**Cost:** ₹0 (all free tier!)

### Step 2: Configure Environment Variables

#### For Local Testing:

```bash
export GEMINI_API_KEY="AIzaSy..."
export GEMINI_API_KEY_2="AIzaSy..."  # Optional backup
export GEMINI_API_KEY_3="AIzaSy..."  # Optional backup
```

#### For Render.com Deployment:

1. Go to your app's dashboard on Render.com
2. Navigate to **"Environment"** tab
3. Add environment variables:
   - Key: `GEMINI_API_KEY`, Value: `AIzaSy...`
   - Key: `GEMINI_API_KEY_2`, Value: `AIzaSy...` (optional)
   - Key: `GEMINI_API_KEY_3`, Value: `AIzaSy...` (optional)
4. Click **"Save Changes"**
5. App will auto-redeploy

### Step 3: Test Locally

```bash
cd streamlit-app
pip install -r requirements.txt
streamlit run app.py
```

**Test checklist:**
- ✅ Open "💡 AI Insights" tab
- ✅ Verify 3 AI insights load (not just math)
- ✅ Try custom question: "Should I increase orders?"
- ✅ Verify AI answer appears

### Step 4: Deploy to Render.com

```bash
git add .
git commit -m "Add real AI insights with Gemini 2.5 Flash + multi-key rotation"
git push origin staging
```

Render.com will auto-deploy!

## How Multi-Key Rotation Works

```python
# Automatic key rotation in utils/ai_insights.py

GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY", ""),       # Primary
    os.getenv("GEMINI_API_KEY_2", ""),     # Backup 1
    os.getenv("GEMINI_API_KEY_3", ""),     # Backup 2
]

def _call_gemini_with_fallback(prompt, max_retries=3):
    for attempt in range(max_retries):
        api_key = _get_next_api_key()  # Round-robin
        try:
            # Call Gemini...
            return response.text
        except Exception:
            # Try next key automatically
            continue
    
    # All keys failed → use text fallback
    return fallback_text
```

## Fallback Behavior

**If all API keys fail or are missing:**
- Pre-built insights → show text summaries (not AI, but functional)
- Custom Q&A → show error: "AI service unavailable"

**App never crashes due to missing API keys!**

## Testing Without API Keys (CI/CD)

Tests in `tests/test_ai_insights.py` verify:
- ✅ Fallback logic works
- ✅ No crashes when keys missing
- ✅ Functions return valid strings

**CI/CD doesn't need API keys to pass tests!**

## Troubleshooting

### Issue: "AI service unavailable"
**Solution:** Check environment variables are set correctly

### Issue: "All API keys exhausted"
**Solution:** 
- Wait 1 minute (15 RPM limit resets)
- Or add more API keys
- Or wait until next day (1,500 RPD limit resets)

### Issue: API keys not working on Render.com
**Solution:** 
1. Verify keys are added in Render.com dashboard
2. Check for typos (keys start with `AIza`)
3. Redeploy app after adding keys

## Cost Analysis

| Scenario | Keys Needed | Cost |
|----------|-------------|------|
| **Week 10 Demo (judges test 50 times)** | 1 key | ₹0 |
| **Week 10 Demo (judges test 200+ times)** | 2-3 keys | ₹0 |
| **Production (100 users/day)** | 2-3 keys | ₹0 |
| **Production (1000+ users/day)** | Paid tier | ~₹500/month |

**For Week 10 demo: 2-3 free keys are MORE than sufficient!**

## RFP Compliance

✅ **RFP Requirement:** "Gemini/Groq AI-powered explanations for 3+ demand scenarios"  
✅ **Our Implementation:** 3 pre-built AI insights + custom Q&A (goes beyond!)

✅ **RFP Evidence:** Screenshots will show REAL AI text (not math formulas)

✅ **Budget:** ₹0 spent (all free tier)

## Advanced Features (Phase 2 - Week 11-16)

Potential enhancements documented in submission Section 9:

1. **AI-Generated Smart Questions:**
   - Gemini suggests 3 relevant questions based on forecast data
   - User clicks to auto-answer

2. **Conversation History:**
   - Multi-turn Q&A (follow-up questions)
   - Context retention

3. **Export AI Insights:**
   - Download AI explanations as PDF report
   - Email to stakeholders

**These are NOT needed for Week 10!**
