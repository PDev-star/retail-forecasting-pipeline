# test_gateway.py - Unit tests for FastAPI Gateway
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


def test_root_endpoint():
    """Test the root endpoint returns correct info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Retail Forecast API"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


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


@patch("api_gateway.requests.post")
def test_ai_insights_success(mock_post):
    """Test successful /ai-insights call with mocked Delta Lake response"""
    # Mock Databricks SQL Execution API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"state": "SUCCEEDED"},
        "result": {
            "manifest": {
                "schema": {
                    "columns": [
                        {"name": "scenario_id"},
                        {"name": "scenario_name"},
                        {"name": "ai_provider"},
                        {"name": "prompt_type"},
                        {"name": "question"},
                        {"name": "context_table"},
                        {"name": "explanation"},
                        {"name": "generated_at"},
                    ]
                }
            },
            "data_array": [
                [
                    1,
                    "Forecast Interpretation",
                    "Gemini 2.5 Flash",
                    "data_explanation",
                    "What do the forecast numbers tell us?",
                    "workspace.default.forecasts",
                    "This forecast shows an upward trend with increasing demand over the next 14 days.",
                    "2026-08-10T12:00:00",
                ],
                [
                    2,
                    "Safety Stock Analysis",
                    "Gemini 2.5 Flash",
                    "inventory_explanation",
                    "How much safety stock do we need?",
                    "workspace.default.stock_levels",
                    "Safety stock provides buffer against demand variability and supply delays.",
                    "2026-08-10T12:00:00",
                ],
                [
                    3,
                    "What-If Scenarios",
                    "Gemini 2.5 Flash",
                    "risk_explanation",
                    "What if we change service level?",
                    "workspace.default.scenarios",
                    "Service level trade-offs affect safety stock requirements and cost.",
                    "2026-08-10T12:00:00",
                ],
            ],
        },
    }
    mock_post.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["success"] is True
    assert data["total"] == 3
    assert len(data["insights"]) == 3
    assert data["cached"] is True
    assert "generated_at" in data

    # Verify first insight
    first_insight = data["insights"][0]
    assert first_insight["scenario_id"] == 1
    assert first_insight["scenario_name"] == "Forecast Interpretation"
    assert first_insight["ai_provider"] == "Gemini 2.5 Flash"
    assert "forecast" in first_insight["explanation"].lower()


@patch("api_gateway.requests.post")
def test_ai_insights_filter_by_scenario(mock_post):
    """Test /ai-insights with scenario_id filter"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"state": "SUCCEEDED"},
        "result": {
            "manifest": {
                "schema": {
                    "columns": [
                        {"name": "scenario_id"},
                        {"name": "scenario_name"},
                        {"name": "ai_provider"},
                        {"name": "prompt_type"},
                        {"name": "question"},
                        {"name": "context_table"},
                        {"name": "explanation"},
                        {"name": "generated_at"},
                    ]
                }
            },
            "data_array": [
                [
                    2,
                    "Safety Stock Analysis",
                    "Gemini 2.5 Flash",
                    "inventory_explanation",
                    "How much safety stock?",
                    "workspace.default.stock_levels",
                    "Safety stock explanation...",
                    "2026-08-10T12:00:00",
                ]
            ],
        },
    }
    mock_post.return_value = mock_response

    response = client.get("/ai-insights?scenario_id=2", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 1
    assert data["insights"][0]["scenario_id"] == 2


@patch("api_gateway.requests.post")
def test_ai_insights_empty_cache(mock_post):
    """Test /ai-insights when Delta Lake table is empty"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"state": "SUCCEEDED"},
        "result": {
            "manifest": {
                "schema": {
                    "columns": [
                        {"name": "scenario_id"},
                        {"name": "scenario_name"},
                        {"name": "ai_provider"},
                        {"name": "prompt_type"},
                        {"name": "question"},
                        {"name": "context_table"},
                        {"name": "explanation"},
                        {"name": "generated_at"},
                    ]
                }
            },
            "data_array": [],
        },
    }
    mock_post.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 0
    assert len(data["insights"]) == 0


@patch("api_gateway.requests.post")
def test_ai_insights_database_error(mock_post):
    """Test /ai-insights handles database connection errors"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 502
    assert "Delta Lake query failed" in response.json()["detail"]


@patch("api_gateway.requests.post")
def test_ai_insights_query_failed(mock_post):
    """Test /ai-insights handles failed query execution"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"state": "FAILED"}, "result": None}
    mock_post.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 502
    assert "execution failed" in response.json()["detail"]


@patch("api_gateway.requests.post")
def test_ai_insights_connection_timeout(mock_post):
    """Test /ai-insights handles connection timeouts"""
    mock_post.side_effect = requests.Timeout("Connection timeout")

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 503
    assert "connection error" in response.json()["detail"].lower()


@patch("api_gateway.requests.post")
def test_ai_insights_malformed_response(mock_post):
    """Test /ai-insights handles malformed database responses"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Has 'result' but missing nested 'manifest' key - will cause KeyError when accessing schema
    mock_response.json.return_value = {
        "status": {"state": "SUCCEEDED"},
        "result": {"data_array": []}  # Missing 'manifest' key
    }
    mock_post.return_value = mock_response

    response = client.get("/ai-insights", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 500
    assert "parsing error" in response.json()["detail"].lower()
