import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from producer/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# Kafka configuration
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Topics
ORDERS_TOPIC = "orders_raw"
PAYMENTS_TOPIC = "payments_raw"

# Producer settings
STREAM_INTERVAL = 1  # seconds between events