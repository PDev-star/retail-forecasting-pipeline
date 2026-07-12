# GitHub Secrets Configuration Guide

## Required GitHub Secrets

Configure these in: **GitHub Repo → Settings → Secrets and variables → Actions**

---

## Production Secrets

### 1. `RENDER_PROD_DEPLOY_HOOK` (REQUIRED)
**What it is:** Webhook URL from Render.com to trigger production FastAPI deployment

**How to get it:**
1. Go to Render Dashboard: https://dashboard.render.com
2. Select your **production** FastAPI service
3. Settings → Deploy Hook → Copy URL
4. Paste into GitHub secrets

**Example value:**
```
https://api.render.com/deploy/srv-abc123?key=xyz789
```

---

### 2. `FASTAPI_PROD_URL` (REQUIRED)
**What it is:** Public URL of your production FastAPI service on Render

**How to get it:**
1. From Render dashboard, find your production service
2. Copy the URL (something like `https://retail-forecast-api.onrender.com`)

**Example value:**
```
https://retail-forecast-api.onrender.com
```

---

### 3. `API_KEY_PROD` (REQUIRED)
**What it is:** API key that GitHub Actions will use to test the deployed FastAPI

**How to set it:**
- Use one of the API keys from your Render `API_KEYS` environment variable
- Or generate a new one:
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Example value:**
```
xZ9kL2mN4pQ5rS6tU7vW8xY9zA0bC1dE2fG3hI4jK5
```

---

## Workflow Execution Flow

### Production (main branch)
```
1. Push to main
   ↓
2. Run unit tests (Streamlit + FastAPI)
   ↓
3. Deploy FastAPI to Render (via webhook)
   ↓
4. Run integration tests (test deployed FastAPI)
   ↓
5. Streamlit auto-deploys from GitHub ✨
```

---

## Streamlit Cloud Secrets

These are configured **separately** in Streamlit Cloud (not GitHub):

### Production App Secrets
(Streamlit Cloud → Production App → Settings → Secrets)
```toml
fastapi_url = "https://retail-forecast-api.onrender.com"
api_key = "xZ9kL2mN4pQ5rS6tU7vW8xY9zA0bC1dE2fG3hI4jK5"
```
