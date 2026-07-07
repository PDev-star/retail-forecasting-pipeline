# Configuration and constants
import time
from datetime import datetime

import requests
import streamlit as st

# Configuration from Streamlit secrets
FASTAPI_URL = st.secrets.get("fastapi_url", "http://localhost:8000")
API_KEY = st.secrets.get("api_key", "demo-key-12345")

# Product catalog - maps to FastAPI product IDs
PRODUCTS = {
    "Cat1": {
        "name": "WHITE HANGING HEART T-LIGHT HOLDER",
        "sku": "85123A",
        "product_id": "Cat1",  # FastAPI uses product_id instead of endpoint
        "color": "#FF6B6B",
    },
    "Cat2": {
        "name": "JUMBO BAG RED RETROSPOT",
        "sku": "22423",
        "product_id": "Cat2",
        "color": "#4ECDC4",
    },
}


def keep_fastapi_warm():
    """
    Background thread that pings FastAPI every 10 minutes to prevent spin-down.

    Render.com free tier spins down after 15 minutes of inactivity.
    This keeps it awake so users don't experience 30-60s cold starts.
    """
    while True:
        try:
            # Ping the health endpoint
            response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ FastAPI keep-alive ping successful at {datetime.now()}")
            else:
                print(f"⚠ FastAPI ping returned {response.status_code}")
        except Exception as e:
            print(f"✗ FastAPI ping failed: {str(e)}")

        # Wait 10 minutes before next ping
        time.sleep(600)  # 600 seconds = 10 minutes
