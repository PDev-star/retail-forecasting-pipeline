# test_gateway.py - Unit tests for FastAPI Gateway
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_gateway import app, verify_api_key, PRODUCTS

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
    assert "Cat1" in data["products"]
    assert "Cat2" in data["products"]


def test_forecast_missing_api_key():
    """Test forecast endpoint without API key returns 422"""
    response = client.post("/forecast?product_id=Cat1&horizon=14")
    assert response.status_code == 422  # Missing required header


def test_forecast_invalid_api_key():
    """Test forecast endpoint with invalid API key returns 401"""
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
    mock_post.side_effect = Exception("Connection timeout")

    response = client.post("/forecast?product_id=Cat1&horizon=14", headers={"X-API-Key": VALID_TEST_KEY})

    assert response.status_code == 503


def test_products_config():
    """Test product configuration is valid"""
    assert "Cat1" in PRODUCTS
    assert "Cat2" in PRODUCTS
    assert "endpoint" in PRODUCTS["Cat1"]
    assert "name" in PRODUCTS["Cat1"]
