# api_gateway.py - FastAPI Gateway for Databricks Model Serving
# Deploy on Render.com (FREE!)
# Updated: 2026-08-11 - Trigger deployment workflow

import os
from datetime import datetime

import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

# SQL Warehouse for Delta Lake queries
SQL_WAREHOUSE_ID = os.environ.get("SQL_WAREHOUSE_ID", "907cc979fc71d54f")

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
            "GET /ai-insights": "Get Gemini AI explanations from Delta Lake",
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


@app.get("/ai-insights")
async def get_ai_insights(scenario_id: int = None, api_key: str = Header(..., alias="X-API-Key")):
    """
    Get Gemini 2.5 Flash AI explanations from Delta Lake cache.
    
    Args:
        scenario_id: Optional scenario filter (1, 2, or 3)
        api_key: API key for authentication
    
    Returns:
        List of AI insights with scenario metadata
    """
    verify_api_key(api_key)
    
    try:
        # Build SQL query
        base_query = """
            SELECT 
                scenario_id,
                scenario_name,
                ai_provider,
                prompt_type,
                question,
                context_table,
                explanation,
                generated_at
            FROM workspace.default.gemini_ai_explanations
        """
        
        if scenario_id:
            base_query += f" WHERE scenario_id = {scenario_id}"
        
        base_query += " ORDER BY scenario_id"
        
        # Execute via Databricks SQL Execution API
        response = requests.post(
            f"{DATABRICKS_HOST}/api/2.0/sql/statements",
            headers={
                "Authorization": f"Bearer {DATABRICKS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "warehouse_id": SQL_WAREHOUSE_ID,
                "statement": base_query,
                "wait_timeout": "30s"
            },
            timeout=35,
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=502, 
                detail=f"Delta Lake query failed: {response.text}"
            )
        
        result = response.json()
        
        # Check if query succeeded
        if result.get("status", {}).get("state") != "SUCCEEDED":
            raise HTTPException(
                status_code=502,
                detail="Query execution failed"
            )
        
        # Parse results (handle empty results gracefully)
        insights = []
        if "result" in result and "data_array" in result["result"]:
            # Check if manifest exists (it won't if table doesn't exist or is empty)
            if "manifest" in result["result"] and "schema" in result["result"]["manifest"]:
                columns = [col["name"] for col in result["result"]["manifest"]["schema"]["columns"]]
                
                for row in result["result"]["data_array"]:
                    insight = dict(zip(columns, row))
                    insights.append(insight)
        
        # Return results (with helpful message if table doesn't exist)
        if len(insights) == 0:
            return {
                "success": True,
                "total": 0,
                "insights": [],
                "cached": True,
                "message": "No AI insights found. Run the Gemini notebook cells to populate Delta Lake cache.",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "total": len(insights),
            "insights": insights,
            "cached": True,  # Indicates these are pre-generated
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Database connection error: {str(e)}")
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Response parsing error: {str(e)}")
