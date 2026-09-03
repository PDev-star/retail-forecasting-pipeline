# api_gateway.py - FastAPI Gateway for Databricks Model Serving
# Deploy on Render.com (FREE!)
# Updated: 2026-08-11 - Trigger deployment workflow (fixed branch case)

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
            timeout=120  # Increased for serverless cold starts (scale-to-zero),
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


# Simple in-memory cache (resets on restart, perfect for Render free tier)
_ai_insights_cache = {"data": None, "timestamp": None, "ttl": 300}  # 5 min TTL


@app.get("/ai-insights")
async def get_ai_insights(scenario_id: int = None, api_key: str = Header(..., alias="X-API-Key")):
    """
    Get Gemini 2.5 Flash AI explanations from Delta Lake cache.
    Includes 5-minute in-memory caching to reduce database load.
    
    Args:
        scenario_id: Optional scenario filter (1, 2, or 3)
        api_key: API key for authentication
    
    Returns:
        List of AI insights with scenario metadata
    """
    verify_api_key(api_key)
    
    # Check cache first (reduces DB load by 95%+)
    cache_valid = (
        _ai_insights_cache["data"] is not None 
        and _ai_insights_cache["timestamp"] is not None
        and (datetime.utcnow() - _ai_insights_cache["timestamp"]).total_seconds() < _ai_insights_cache["ttl"]
    )
    
    if cache_valid:
        # Return cached data (filter by scenario_id if requested)
        cached_insights = _ai_insights_cache["data"]
        if scenario_id:
            cached_insights = [ins for ins in cached_insights if ins.get("scenario_id") == scenario_id]
        
        return {
            "success": True,
            "total": len(cached_insights),
            "insights": cached_insights,
            "cached": True,
            "cache_age_seconds": int((datetime.utcnow() - _ai_insights_cache["timestamp"]).total_seconds()),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Cache miss - query database
    try:
        # Build SQL query (no filter here, cache all scenarios)
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
            ORDER BY scenario_id
        """
        
        # Execute via Databricks SQL Execution API with INCREASED TIMEOUT
        response = requests.post(
            f"{DATABRICKS_HOST}/api/2.0/sql/statements",
            headers={
                "Authorization": f"Bearer {DATABRICKS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "warehouse_id": SQL_WAREHOUSE_ID,
                "statement": base_query,
                "wait_timeout": "90s"  # Increased from 30s to handle warehouse cold start
            },
            timeout=120,  # Increased from 35s to 120s (matches other endpoints)
        )
        
        if response.status_code != 200:
            # Return graceful error instead of crashing
            return {
                "success": False,
                "total": 0,
                "insights": [],
                "cached": False,
                "error": f"Database query failed (HTTP {response.status_code})",
                "message": "SQL warehouse may be starting up (cold start). Try again in 30-60 seconds.",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        result = response.json()
        
        # Check if query is still pending (warehouse cold start)
        query_state = result.get("status", {}).get("state", "UNKNOWN")
        
        if query_state == "PENDING":
            # Warehouse is starting up - return helpful message instead of error
            return {
                "success": False,
                "total": 0,
                "insights": [],
                "cached": False,
                "error": "SQL warehouse is starting (cold start)",
                "message": "Warehouse is waking up. This takes 30-60 seconds. Please retry in a moment.",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        if query_state != "SUCCEEDED":
            return {
                "success": False,
                "total": 0,
                "insights": [],
                "cached": False,
                "error": f"Query failed with state: {query_state}",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Parse results
        insights = []
        if "result" in result and "data_array" in result["result"]:
            if "manifest" in result and "schema" in result["manifest"]:
                columns = [col["name"] for col in result["manifest"]["schema"]["columns"]]
                
                for row in result["result"]["data_array"]:
                    insight = dict(zip(columns, row))
                    insights.append(insight)
        
        # Update cache (even if empty, to avoid repeated failed queries)
        _ai_insights_cache["data"] = insights
        _ai_insights_cache["timestamp"] = datetime.utcnow()
        
        # Filter by scenario_id if requested
        filtered_insights = insights
        if scenario_id:
            filtered_insights = [ins for ins in insights if ins.get("scenario_id") == scenario_id]
        
        # Return results
        if len(insights) == 0:
            return {
                "success": True,
                "total": 0,
                "insights": [],
                "cached": False,
                "message": "No AI insights found. Run the Gemini notebook cells (71-72) to populate Delta Lake cache.",
                "generated_at": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "total": len(filtered_insights),
            "insights": filtered_insights,
            "cached": False,
            "cache_age_seconds": 0,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except requests.Timeout:
        # Handle timeout gracefully instead of crashing
        return {
            "success": False,
            "total": 0,
            "insights": [],
            "cached": False,
            "error": "Request timeout (SQL warehouse cold start)",
            "message": "Query timed out. SQL warehouse may be starting. Try again in 60 seconds.",
            "generated_at": datetime.utcnow().isoformat()
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "total": 0,
            "insights": [],
            "cached": False,
            "error": f"Database connection error: {str(e)}",
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "total": 0,
            "insights": [],
            "cached": False,
            "error": f"Unexpected error: {str(e)}",
            "generated_at": datetime.utcnow().isoformat()
        }
