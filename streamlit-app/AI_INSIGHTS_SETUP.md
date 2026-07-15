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
5. **IMPORTANT:** For multiple keys, use DIFFERENT Google accounts (keys from same account share quota!)
6. Repeat for 2-3 keys

**Cost:** ₹0 (all free tier!)

### Step 2: Configure Environment Variables

#### For Local Testing:

```bash
export GEMINI_API_KEY="AIzaSy..."
export GEMINI_API_KEY_2="AIzaSy..."  # Optional backup
export GEMINI_API_KEY_3="AIzaSy..."  # Optional backup
```

#### For Streamlit Cloud Deployment:

1. Go to your app's dashboard: https://share.streamlit.io
2. Click on your app → **⚙️ Settings** → **Secrets**
3. Add secrets in TOML format:

```toml
GEMINI_API_KEY = "AIzaSy..."
GEMINI_API_KEY_2 = "AIzaSy..."
GEMINI_API_KEY_3 = "AIzaSy..."
```

4. Click **"Save"**
5. App will auto-redeploy

**⚠️ CRITICAL:** Make sure keys are from DIFFERENT Google accounts, otherwise they share the same quota!

#### For Render.com (FastAPI):

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

### Step 4: Deploy to Staging

```bash
git add .
git commit -m "Add real AI insights with Gemini 2.5 Flash + multi-key rotation"
git push origin staging
```

Streamlit Cloud will auto-deploy!

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
        api_key = _get_next_api_key()
        try:
            # Call Gemini
            return response.text
        except Exception as e:
            # Rate limit hit? Try next key
            continue
    
    # All keys exhausted? Return fallback text
    return "Fallback explanation..."
```

## Troubleshooting

### Issue: "All API keys exhausted"

**Possible causes:**
1. **Keys from same Google account** → They share quota! Use different accounts.
2. **Heavy testing** → Wait 1 minute for RPM quota to reset, or 24h for daily quota.
3. **Keys not configured** → Check Streamlit Cloud secrets panel.
4. **Invalid keys** → Verify at https://aistudio.google.com/apikey

**Solutions:**

1. **Check logs in Streamlit Cloud:**
   - Click app → ⚙️ Settings → Logs
   - Look for: `🔑 Gemini API Keys configured: X`
   - Should see 2-3 keys, not 0!

2. **Verify keys are valid:**
   - Go to https://aistudio.google.com/apikey
   - Check if keys are still active
   - Delete and recreate if needed

3. **Add more keys from different accounts:**
   - Keys from same account = same quota pool
   - Use 2-3 different Google accounts
   - Set GEMINI_API_KEY_2 and GEMINI_API_KEY_3

4. **Wait for quota reset:**
   - RPM (requests per minute): Resets every minute
   - RPD (requests per day): Resets at midnight UTC

### Issue: Tab reloads unexpectedly

**Cause:** Streamlit re-renders entire app when state changes or errors occur.

**Solution:** This is normal Streamlit behavior. Just click back to "AI Insights" tab.

## Quota Calculator

**Free tier per key:**
- 15 requests/minute
- 1,500 requests/day

**With 3 keys:**
- 45 requests/minute
- 4,500 requests/day

**Each forecast generates:**
- 3 pre-built insights = 3 API calls
- 1 custom question = 1 API call

**Example usage:**
- 10 forecasts/hour = 30 API calls = Fits in free tier easily!
- 100 forecasts/day = 300 API calls = Well within daily limit!

## Architecture

```
User clicks "Get AI Answer"
    ↓
Streamlit app → ai_insights.py
    ↓
_call_gemini_with_fallback()
    ↓
Try Key #1 → Rate limit? → Try Key #2 → Rate limit? → Try Key #3 → All failed?
    ↓                          ↓                          ↓                ↓
  Success!                  Success!                  Success!        Fallback text
```

## API Response Times

- **Gemini 2.5 Flash:** 1-3 seconds per call
- **Pre-built insights:** ~3-9 seconds (3 parallel calls)
- **Custom Q&A:** 1-3 seconds

## Security

✅ API keys stored in environment variables (never in code)
✅ Keys are masked in logs (first 8 + last 4 chars shown)
✅ No user input goes to logs (only prompt templates)

## Cost

**Everything is FREE!** 🎉

- Gemini 2.5 Flash: Free tier (1,500 requests/day per key)
- Streamlit Cloud: Free hosting
- GitHub Actions: Free CI/CD

---

**For questions or issues, check:**
1. Streamlit Cloud logs
2. Gemini API console: https://aistudio.google.com/apikey
3. Rate limits: https://ai.google.dev/pricing
