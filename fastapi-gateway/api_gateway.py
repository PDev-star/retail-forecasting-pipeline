# api_gateway.py - FastAPI Gateway for Databricks Model Serving
# Deploy on Render.com (FREE!)

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from datetime import datetime

app = FastAPI(
    title="Retail Forecast API Gateway",
    description="Public API for demand forecasting",
    version="1.0.0",
)

# CORS - Allow external apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config from environment variables (set in Render.com)
DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "https://dbc-7e8a8bf0-dc9f.cloud.databricks.com")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
VALID_API_KEYS = set(os.environ.get("API_KEYS", "demo-key-12345").split(","))

PRODUCTS = {
    "Cat1": {"name": "WHITE HANGING HEART T-LIGHT HOLDER", "endpoint": "Cat1Forecast"},
    "Cat2": {"name": "JUMBO BAG RED RETROSPOT", "endpoint": "Cat2Forecast"},
}


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.get("/")
async def root():
    return {
        "service": "Retail Forecast API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "POST /forecast": "Get demand forecast",
            "GET /products": "List products",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/products")
async def list_products():
    return {"products": list(PRODUCTS.keys())}


@app.post("/forecast")
async def get_forecast(product_id: str, horizon: int = 14, api_key: str = Header(..., alias="X-API-Key")):
    """Get demand forecast for a product"""
    verify_api_key(api_key)

    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")

    if not (7 <= horizon <= 90):
        raise HTTPException(status_code=400, detail="Horizon must be 7-90 days")

    product = PRODUCTS[product_id]

    try:
        response = requests.post(
            f"{DATABRICKS_HOST}/serving-endpoints/{product['endpoint']}/invocations",
            headers={
                "Authorization": f"Bearer {DATABRICKS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"dataframe_records": [{"h": horizon}]},
            timeout=60,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Model serving error")

        data = response.json()
        forecast_values = [pred["AutoETS"] for pred in data["predictions"]]

        return {
            "success": True,
            "product": {"id": product_id, "name": product["name"]},
            "forecast": {"horizon_days": horizon, "values": forecast_values},
            "generated_at": datetime.utcnow().isoformat(),
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))
