# Deployment Guide: FastAPI + Streamlit Proxy Architecture

## Architecture Overview

```
┌─────────────────┐     API Key      ┌──────────────┐   Databricks Token   ┌────────────────┐
│  Streamlit App  │ ───────────────> │   FastAPI    │ ──────────────────> │  Databricks    │
│   (Frontend)    │  (X-API-Key)     │   Gateway    │  (Bearer Token)     │ Model Serving  │
└─────────────────┘                  └──────────────┘                      └────────────────┘
      Public                               Proxy                                  Private
                                            
     ✅ No Databricks credentials         ✅ API Key Auth                ✅ Databricks Credentials
                                          ✅ Rate Limiting               ✅ Model Endpoints
                                          ✅ Logging                     ✅ Delta Lake
```

## What Changed

### Before (Direct Connection)
- Streamlit had Databricks credentials
- Direct calls to Model Serving endpoints
- ❌ Credentials exposed to frontend

### After (Proxy Pattern)  
- Streamlit only has API key
- Calls FastAPI, which proxies to Databricks
- ✅ Credentials isolated server-side
- ✅ Revocable API keys
- ✅ Centralized monitoring

## Step-by-Step Deployment

### Step 1: Deploy FastAPI Gateway (Render.com - FREE)

1. **Push code to GitHub**
   ```bash
   git push origin main
   ```

2. **Create Render account**: https://render.com

3. **New Web Service**:
   - Connect GitHub repository
   - **Root Directory**: `fastapi-gateway`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api_gateway:app --host 0.0.0.0 --port $PORT`

4. **Environment Variables** (in Render dashboard):
   ```
   DATABRICKS_HOST=https://dbc-7e8a8bf0-dc9f.cloud.databricks.com
   DATABRICKS_TOKEN=dapi...  (get from Databricks User Settings)
   API_KEYS=secret-key-123,secret-key-456  (generate secure keys - see below)
   ```

5. **Deploy** - Render gives you URL: `https://retail-forecast-api.onrender.com`

**Generate Secure API Keys**:
```python
import secrets
print(secrets.token_urlsafe(32))
# Example: 'xZ9kL2mN4pQ5rS6tU7vW8xY9zA0bC1dE2fG3hI4jK5'
```

---

### Step 2: Update Streamlit App Configuration

1. **Create/Update `.streamlit/secrets.toml`**:
   ```toml
   # OLD (remove these):
   # databricks_token = "dapi..."  ❌
   # databricks_host = "https://..."  ❌
   
   # NEW (use these):
   fastapi_url = "https://retail-forecast-api.onrender.com"
   api_key = "secret-key-123"  # One of the keys from FastAPI
   ```

2. **For Streamlit Cloud**:
   - Go to app settings
   - Secrets section
   - Paste the content above
   - Delete old Databricks credentials

---

### Step 3: Deploy Streamlit App (Streamlit Cloud)

1. **Push updated code to GitHub**
   ```bash
   git add streamlit-app/app.py
   git commit -m "Refactor: Use FastAPI proxy instead of direct Databricks"
   git push origin main
   ```

2. **Create Streamlit Cloud app** (or update existing):
   - Connect GitHub repo
   - **Main file path**: `streamlit-app/app.py`
   - **Secrets**: Set `fastapi_url` and `api_key` (see Step 2)

3. **Deploy**

---

### Step 4: Test End-to-End

1. **Test FastAPI directly**:
   ```bash
   curl -X POST "https://retail-forecast-api.onrender.com/forecast?product_id=Cat1&horizon=14"      -H "X-API-Key: secret-key-123"
   ```

   Expected response:
   ```json
   {
     "success": true,
     "product": {"id": "Cat1", "name": "WHITE HANGING HEART T-LIGHT HOLDER"},
     "forecast": {
       "horizon_days": 14,
       "values": [45.2, 48.1, 52.3, ...]
     }
   }
   ```

2. **Test Streamlit app**:
   - Visit: `https://your-app.streamlit.app`
   - Select a product
   - Click "🔮 Generate Forecast"
   - Should work! ✅

---

## Local Development

### Terminal 1: FastAPI
```bash
cd fastapi-gateway
export DATABRICKS_HOST="https://dbc-7e8a8bf0-dc9f.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
export API_KEYS="test-key-123"
uvicorn api_gateway:app --reload

# Running at: http://localhost:8000
```

### Terminal 2: Streamlit
```bash
cd streamlit-app

# Create .streamlit/secrets.toml:
# fastapi_url = "http://localhost:8000"
# api_key = "test-key-123"

streamlit run app.py

# Running at: http://localhost:8501
```

---

## Troubleshooting

### ❌ "Invalid API key"
- Check `X-API-Key` header in Streamlit secrets
- Verify key is in FastAPI `API_KEYS` environment variable

### ❌ "Cannot connect to FastAPI Gateway"
- Check `fastapi_url` in Streamlit secrets
- Verify FastAPI is running (visit `/health` endpoint)
- Check network/firewall

### ❌ "502 Bad Gateway"
- Check Databricks token is valid
- Verify Model Serving endpoints are running
- Check Databricks workspace URL

---

## Security Best Practices

### API Key Management
- ✅ Generate cryptographically secure keys
- ✅ Rotate keys quarterly
- ✅ Use different keys per client/environment
- ✅ Monitor usage per key
- ✅ Revoke compromised keys immediately

### Databricks Token
- ✅ Use service account token (not personal)
- ✅ Scope to minimum permissions (Model Serving only)
- ✅ Rotate annually
- ✅ Store in environment variables (never in code)

---

## Benefits Demonstrated

✅ **Security**: Databricks credentials isolated server-side  
✅ **Decoupling**: Frontend doesn't need Databricks SDK  
✅ **Scalability**: Multiple clients via single gateway  
✅ **Monitoring**: Centralized logging and access control  
✅ **Best Practices**: Industry-standard API gateway pattern  
✅ **Production-Ready**: Deployed on reliable cloud platforms

This architecture is perfect for:
- Public-facing ML applications
- Third-party integrations
- Mobile app backends
- Multi-tenant deployments

---

## Next Steps

1. ✅ Deploy FastAPI to Render.com
2. ✅ Update Streamlit secrets
3. ✅ Deploy Streamlit to Streamlit Cloud
4. ✅ Test end-to-end
5. 🚀 Add rate limiting (optional)
6. 🚀 Add response caching (optional)
7. 🚀 Add monitoring/alerting (optional)

**You now have a production-ready, secure ML API gateway!** 🎉
