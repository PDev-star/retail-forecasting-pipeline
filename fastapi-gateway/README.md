# FastAPI Gateway - Retail Forecasting API

Public REST API for external applications to access demand forecasts.

## Deploy on Render.com (FREE!)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "FastAPI gateway"
git remote add origin https://github.com/YOUR_USERNAME/retail-forecast-api.git
git push -u origin main
```

### 2. Deploy on Render.com

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Settings:
   - Name: retail-forecast-api
   - Environment: Python 3
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn api_gateway:app --host 0.0.0.0 --port $PORT`
   - Instance: FREE
5. Environment Variables:
   - DATABRICKS_HOST = https://dbc-7e8a8bf0-dc9f.cloud.databricks.com
   - DATABRICKS_TOKEN = dapi...
   - API_KEYS = your-secret-key-123,another-key-456
6. Deploy!

**API URL:** https://retail-forecast-api.onrender.com

## Usage

### Python
```python
import requests

response = requests.post(
    "https://retail-forecast-api.onrender.com/forecast",
    params={"product_id": "Cat1", "horizon": 14},
    headers={"X-API-Key": "your-secret-key-123"}
)
print(response.json())
```

### cURL
```bash
curl -X POST "https://retail-forecast-api.onrender.com/forecast?product_id=Cat1&horizon=14" \
  -H "X-API-Key: your-secret-key-123"
```

## Cost

- **FREE** (750 hrs/month on Render.com)
- No credit card required

<!-- Trigger CI for workflow changes -->
