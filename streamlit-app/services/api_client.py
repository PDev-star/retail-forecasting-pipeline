# API client for FastAPI gateway
import requests
import streamlit as st

from utils.config import FASTAPI_URL, API_KEY


def get_forecast(product_id, horizon):
    """
    Call FastAPI Gateway to get forecast.

    This function calls the FastAPI gateway which:
    1. Validates the API key
    2. Proxies the request to Databricks Model Serving
    3. Returns the forecast

    Benefits:
    - NO Databricks credentials needed in Streamlit!
    - API key-based authentication (secure for public apps)
    - Rate limiting and monitoring at gateway level
    - Decouples frontend from Databricks infrastructure
    """
    try:
        response = requests.post(
            f"{FASTAPI_URL}/forecast",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json",
            },
            params={
                "product_id": product_id,
                "horizon": horizon,
            },
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            # Extract forecast values from FastAPI response
            forecast_values = data["forecast"]["values"]
            return forecast_values
        elif response.status_code == 401:
            st.error("🔒 Invalid API key. Please check your credentials.")
            return None
        elif response.status_code == 404:
            st.error(f"❌ Product '{product_id}' not found.")
            return None
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        st.error(f"🔌 Cannot connect to FastAPI Gateway at {FASTAPI_URL}. Is the server running?")
        return None
    except Exception as e:
        st.error(f"Error calling FastAPI: {str(e)}")
        return None
