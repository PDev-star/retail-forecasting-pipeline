# Configuration and constants
import time
from datetime import datetime

import requests

# Conditional streamlit import - tests run without streamlit
try:
    import streamlit as st
    FASTAPI_URL = st.secrets.get("fastapi_url", "http://localhost:8000")
    API_KEY = st.secrets.get("api_key", "demo-key-12345")
except (ImportError, AttributeError, FileNotFoundError):
    # Test environment - use defaults (no secrets file or streamlit not available)
    FASTAPI_URL = "http://localhost:8000"
    API_KEY = "demo-key-12345"

# Product catalog - maps to FastAPI product IDs
PRODUCTS = {
    "Cat1": {
        "name": "WHITE HANGING HEART T-LIGHT HOLDER",
        "sku": "22469",
        "product_id": "Cat1",
        "color": "#FF6B6B"
    },
    "Cat2": {
        "name": "JUMBO BAG RED RETROSPOT",
        "sku": "22083",
        "product_id": "Cat2",
        "color": "#4ECDC4"
    }
}


def keep_fastapi_warm(fastapi_url: str = None, interval_seconds: int = 300, max_iterations: int = 100):
    """
    Background thread function to ping FastAPI endpoint every interval_seconds.
    Prevents Render free tier from cold starting (15 min idle timeout).
    
    Args:
        fastapi_url: Base URL of FastAPI service (default: uses global FASTAPI_URL)
        interval_seconds: Seconds between pings (default 5 min)
        max_iterations: Max pings before stopping (default 100)
    """
    if fastapi_url is None:
        fastapi_url = FASTAPI_URL
    
    iteration = 0
    while iteration < max_iterations:
        try:
            response = requests.get(f"{fastapi_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ FastAPI keep-alive ping #{iteration + 1}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  FastAPI returned {response.status_code}")
        except Exception as e:
            # Catch all exceptions to prevent keep-alive thread from crashing
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ FastAPI keep-alive failed: {e}")
        
        time.sleep(interval_seconds)
        iteration += 1
