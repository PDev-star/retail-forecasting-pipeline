# test_gateway.py - Unit tests for FastAPI Gateway
# Trigger deployment workflow
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_gateway import PRODUCTS, app, verify_api_key
import api_gateway

client = TestClient(app)

# Test Data
VALID_TEST_KEY = "test-key-123"
INVALID_KEY = "invalid-key"


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")
    monkeypatch.setenv("API_KEYS", VALID_TEST_KEY)
    
    # FIXED: Update the VALID_API_KEYS set that's already been loaded
    api_gateway.VALID_API_KEYS = {VALID_TEST_KEY}
    
    # Clear cache between tests to avoid pollution
    api_gateway._ai_insights_cache["data"] = None
    api_gateway._ai_insights_cache["timestamp"] = None
    
    # Clear warmup status between tests
    api_gateway._warmup_status["completed"] = False
    api_gateway._warmup_status["in_progress"] = False
    api_gateway._warmup_status["last_attempt"] = None
    api_gateway._warmup_status["error"] = None


def test_root_endpoint():
    """Test the root endpoint returns correct info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Retail Forecast API"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data


def test_health_endpoint():
    """Test health check endpoint with new cache status fields"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    # New fields from warmup implementation
    assert "cache_populated" in data
    assert "cache_size" in data
    assert "warmup_completed" in data
    assert isinstance(data["cache_populated"], bool)
    assert isinstance(data["cache_size"], int)


def test_list_products():
    """Test products listing endpoint"""
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert len(data["products"]) == 2


def test_forecast_missing_api_key():
    """Test forecast without API key returns 401"""
    response = client.post("/forecast?product_id=Cat1&horizon=14")
    assert response.status_code == 422  # FastAPI validation error


def test_forecast_invalid_api_key():
    """Test forecast with invalid API key returns 401"""
    response = client.post("/forecast?product_id=Cat1&horizon=14", headers={"X-API-Key": INVALID_KEY})
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


def test_forecast_invalid_product():
    """Test forecast with invalid product ID returns 404"""
    response = client.post(
        "/forecast?product_id=InvalidProduct&horizon=14",
        headers={"X-API-Key": VALID_TEST_KEY},
    )
    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]


def test_forecast_invalid_horizon():
    """Test forecast with invalid horizon returns 400"""
    # Too low
    response = client.post("/forecast?product_id=Cat1&horizon=5", headers={"X-API-Key": VALID_TEST_KEY})
    assert response.status_code == 400

    # Too high
    response = client.post("/forecast?product_id=Cat1&horizon=100", headers={"X-API-Key": VALID_TEST_KEY})
    assert response.status_code == 400


@patch("api_gateway.requests.post")
def test_forecast_success(mock_post):
    """Test successful forecast request"""
    # Mock Databricks response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"predictions": [{"AutoETS": 45.2}, {"AutoETS": 43.8}, {"AutoETS": 44.1}]}
    mock_post.return_value = mock_response

    response = client.post("/forecast?product_id=Cat1&horizon=14", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["product"]["id"] == "Cat1"
    assert data["forecast"]["horizon_days"] == 14
    assert len(data["forecast"]["values"]) == 3
    assert data["forecast"]["values"][0] == 45.2


@patch("api_gateway.requests.post")
def test_forecast_databricks_error(mock_post):
    """Test handling of Databricks endpoint error"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_post.return_value = mock_response

    response = client.post("/forecast?product_id=Cat1&horizon=14", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 502


@patch("api_gateway.requests.post")
def test_forecast_timeout(mock_post):
    """Test handling of request timeout"""
    # FIXED: Use requests.Timeout instead of generic Exception
    mock_post.side_effect = requests.Timeout("Connection timeout")

    response = client.post("/forecast?product_id=Cat1&horizon=14", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 503


def test_products_config():
    """Test product configuration is valid"""
    assert "Cat1" in PRODUCTS
    assert "Cat2" in PRODUCTS
    assert "endpoint" in PRODUCTS["Cat1"]
    assert "name" in PRODUCTS["Cat1"]


# =========================================================================
# TESTS FOR /ai-insights ENDPOINT (GEMINI INTEGRATION)
# =========================================================================

def test_ai_insights_missing_api_key():
    """Test /ai-insights rejects requests without API key"""
    response = client.get("/ai-insights")
    assert response.status_code == 422  # FastAPI validation error


def test_ai_insights_invalid_api_key():
    """Test /ai-insights rejects invalid API key"""
    response = client.get("/ai-insights", headers={"X-API-Key": INVALID_KEY})
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


@patch("api_gateway.requests.get")
def test_ai_insights_success(mock_get):
    """Test successful /ai-insights call with mocked UC Volume response"""
    # Mock Databricks Files API response (UC Volume - returns JSON directly, not base64)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "total": 3,
        "insights": [
            {
                "scenario_id": 1,
                "scenario_name": "Forecast Interpretation",
                "ai_provider": "Gemini 2.5 Flash",
                "prompt_type": "data_explanation",
                "question": "What do the forecast numbers tell us?",
                "context_table": "workspace.default.forecasts",
                "explanation": "This forecast shows an upward trend with increasing demand over the next 14 days.",
                "generated_at": "2026-08-10T12:00:00",
            },
            {
                "scenario_id": 2,
                "scenario_name": "Safety Stock Analysis",
                "ai_provider": "Gemini 2.5 Flash",
                "prompt_type": "inventory_explanation",
                "question": "How much safety stock do we need?",
                "context_table": "workspace.default.stock_levels",
                "explanation": "Safety stock provides buffer against demand variability and supply delays.",
                "generated_at": "2026-08-10T12:00:00",
            },
            {
                "scenario_id": 3,
                "scenario_name": "What-If Scenarios",
                "ai_provider": "Gemini 2.5 Flash",
                "prompt_type": "risk_explanation",
                "question": "What if we change service level?",
                "context_table": "workspace.default.scenarios",
                "explanation": "Service level trade-offs affect safety stock requirements and cost.",
                "generated_at": "2026-08-10T12:00:00",
            },
        ],
        "cached": True,
        "generated_at": "2026-08-10T12:00:00",
        "cache_age_seconds": 0,
    }
    mock_get.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["success"] is True
    assert data["total"] == 3
    assert len(data["insights"]) == 3
    assert data["cached"] is False  # First call is not cached
    assert "generated_at" in data

    # Verify first insight
    first_insight = data["insights"][0]
    assert first_insight["scenario_id"] == 1
    assert first_insight["scenario_name"] == "Forecast Interpretation"
    assert first_insight["ai_provider"] == "Gemini 2.5 Flash"
    assert "forecast" in first_insight["explanation"].lower()


@patch("api_gateway.requests.get")
def test_ai_insights_filter_by_scenario(mock_get):
    """Test /ai-insights with scenario_id filter"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "total": 3,
        "insights": [
            {
                "scenario_id": 1,
                "scenario_name": "Forecast Interpretation",
                "ai_provider": "Gemini 2.5 Flash",
                "explanation": "Forecast explanation",
            },
            {
                "scenario_id": 2,
                "scenario_name": "Safety Stock Analysis",
                "ai_provider": "Gemini 2.5 Flash",
                "explanation": "Safety stock explanation",
            },
            {
                "scenario_id": 3,
                "scenario_name": "What-If Scenarios",
                "ai_provider": "Gemini 2.5 Flash",
                "explanation": "Scenario explanation",
            },
        ],
        "cached": True,
    }
    mock_get.return_value = mock_response

    response = client.get("/ai-insights?scenario_id=2", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 1
    assert data["insights"][0]["scenario_id"] == 2


@patch("api_gateway.requests.get")
def test_ai_insights_empty_cache(mock_get):
    """Test /ai-insights when UC Volume cache file is empty"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "total": 0,
        "insights": [],
        "cached": True,
        "generated_at": "2026-09-03T12:00:00",
    }
    mock_get.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 0
    assert len(data["insights"]) == 0


@patch("api_gateway.requests.get")
def test_ai_insights_file_not_found(mock_get):
    """Test /ai-insights handles UC Volume file not found (404)"""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    # Returns 200 with success=false and helpful message
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Cache file not found" in data["error"]


@patch("api_gateway.requests.get")
def test_ai_insights_connection_timeout(mock_get):
    """Test /ai-insights handles connection timeouts"""
    mock_get.side_effect = requests.Timeout("Connection timeout")

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    # Returns 200 with success=false instead of HTTP error
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "timeout" in data["error"].lower()


@patch("api_gateway.requests.get")
def test_ai_insights_malformed_response(mock_get):
    """Test /ai-insights gracefully handles malformed UC Volume JSON"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Missing 'insights' key - will cause validation error
    mock_response.json.return_value = {
        "success": True,
        "total": 0,
        # Missing 'insights' key
    }
    mock_get.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    # Should gracefully return 200 with error message
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Invalid cache file format" in data["error"]


# =========================================================================
# TESTS FOR NEW WARMUP ENDPOINTS (CACHE-STATUS, WARMUP, STARTUP)
# =========================================================================

def test_cache_status_endpoint():
    """Test /cache-status endpoint returns cache and warmup info"""
    response = client.get("/cache-status")
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "cache" in data
    assert "warmup" in data
    assert "timestamp" in data
    
    # Cache fields
    assert "populated" in data["cache"]
    assert "size" in data["cache"]
    assert "age_seconds" in data["cache"]
    assert "ttl_seconds" in data["cache"]
    assert "expires_in_seconds" in data["cache"]
    
    # Warmup fields
    assert "completed" in data["warmup"]
    assert "in_progress" in data["warmup"]
    assert "last_attempt" in data["warmup"]
    assert "error" in data["warmup"]


def test_warmup_endpoint_trigger():
    """Test /warmup endpoint triggers background warmup"""
    response = client.get("/warmup")
    assert response.status_code == 200
    data = response.json()
    
    # Should indicate warmup was triggered
    assert "status" in data
    assert data["status"] in ["triggered", "already_running"]
    assert "message" in data


def test_warmup_endpoint_already_running():
    """Test /warmup endpoint when warmup is already in progress"""
    # Set warmup to in_progress
    api_gateway._warmup_status["in_progress"] = True
    
    response = client.get("/warmup")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "already_running"
    assert "already in progress" in data["message"].lower()
    
    # Clean up
    api_gateway._warmup_status["in_progress"] = False


@patch("api_gateway.requests.get")
def test_ai_insights_cache_hit(mock_get):
    """Test /ai-insights returns cached data without UC Volume call"""
    from datetime import datetime
    
    # Pre-populate cache
    api_gateway._ai_insights_cache["data"] = [
        {
            "scenario_id": 1,
            "scenario_name": "Cached Scenario",
            "ai_provider": "Gemini 2.5 Flash",
            "prompt_type": "test",
            "question": "Test question?",
            "context_table": "test_table",
            "explanation": "Cached explanation",
            "generated_at": "2026-09-03T12:00:00"
        }
    ]
    api_gateway._ai_insights_cache["timestamp"] = datetime.utcnow()
    
    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})
    
    # Should return cached data without calling UC Volume
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["cached"] is True
    assert data["total"] == 1
    assert data["insights"][0]["scenario_name"] == "Cached Scenario"
    
    # Verify no UC Volume call was made
    mock_get.assert_not_called()


@patch("api_gateway.requests.post")
def test_ai_insights_stale_cache_revalidate(mock_post):
    """Test stale-while-revalidate: returns stale data, fetches fresh in background"""
    from datetime import datetime, timedelta
    
    # Pre-populate cache with stale data (7 minutes old, > 5 min TTL but < 1 hr stale_ttl)
    api_gateway._ai_insights_cache["data"] = [
        {
            "scenario_id": 1,
            "scenario_name": "Stale Scenario",
            "ai_provider": "Gemini 2.5 Flash",
            "prompt_type": "test",
            "question": "Old question?",
            "context_table": "test_table",
            "explanation": "Stale explanation",
            "generated_at": "2026-09-03T12:00:00"
        }
    ]
    api_gateway._ai_insights_cache["timestamp"] = datetime.utcnow() - timedelta(minutes=7)
    
    # Mock fast-failing DB call (warehouse cold start)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"state": "PENDING"}  # Warehouse still warming up
    }
    mock_post.return_value = mock_response
    
    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})
    
    # Should return stale cached data immediately
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["cached"] is True
    assert data["stale"] is True  # Indicates stale-while-revalidate
    assert "Serving cached data" in data.get("message", "")
    assert data["insights"][0]["scenario_name"] == "Stale Scenario"


# Test removed: test_ai_insights_warehouse_cold_start
# No longer relevant - UC Volume has no warehouse cold starts!


@patch("api_gateway.requests.get")
def test_warmup_cache_background_success(mock_get):
    """Test warmup_cache_background populates cache successfully from UC Volume"""
    import asyncio
    
    # Mock successful UC Volume response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "total": 1,
        "insights": [
            {
                "scenario_id": 1,
                "scenario_name": "Warmup Scenario",
                "ai_provider": "Gemini 2.5 Flash",
                "prompt_type": "test",
                "question": "Warmup test?",
                "context_table": "test_table",
                "explanation": "Warmup explanation",
                "generated_at": "2026-09-03T12:00:00",
            }
        ],
    }
    mock_get.return_value = mock_response
    
    # Run warmup in event loop
    asyncio.run(api_gateway.warmup_cache_background())
    
    # Verify cache was populated
    assert api_gateway._ai_insights_cache["data"] is not None
    assert len(api_gateway._ai_insights_cache["data"]) == 1
    assert api_gateway._warmup_status["completed"] is True
    assert api_gateway._warmup_status["error"] is None


@patch("api_gateway.requests.get")
def test_warmup_cache_background_timeout(mock_get):
    """Test warmup_cache_background handles timeout gracefully"""
    import asyncio
    
    # Mock timeout
    mock_get.side_effect = requests.Timeout("Connection timeout")
    
    # Run warmup in event loop
    asyncio.run(api_gateway.warmup_cache_background())
    
    # Verify warmup recorded error but didn't crash
    assert api_gateway._warmup_status["completed"] is False
    assert api_gateway._warmup_status["error"] is not None
    assert "timeout" in api_gateway._warmup_status["error"].lower()


# Test removed: test_warmup_cache_background_warehouse_cold_start
# No longer relevant - UC Volume has no warehouse cold starts!


@patch("api_gateway.requests.get")
def test_warmup_cache_background_http_error(mock_get):
    """Test warmup_cache_background handles HTTP errors from UC Volume"""
    import asyncio
    
    # Mock HTTP error (e.g., 404 file not found)
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    # Run warmup in event loop
    asyncio.run(api_gateway.warmup_cache_background())
    
    # Verify warmup recorded error but didn't crash
    assert api_gateway._warmup_status["completed"] is False
    assert api_gateway._warmup_status["error"] is not None
    assert "404" in api_gateway._warmup_status["error"]


def test_warmup_cache_background_skip_if_in_progress():
    """Test warmup_cache_background skips if already running"""
    import asyncio
    
    # Set warmup to in_progress
    api_gateway._warmup_status["in_progress"] = True
    
    # Run warmup - should return immediately
    asyncio.run(api_gateway.warmup_cache_background())
    
    # Should still be in_progress (no state change)
    assert api_gateway._warmup_status["in_progress"] is True
    
    # Clean up
    api_gateway._warmup_status["in_progress"] = False
