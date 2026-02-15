import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (three levels up from backend/consumer/)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

# Kafka configuration
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Topics (must match producer)
ORDERS_TOPIC = "orders_raw"
PAYMENTS_TOPIC = "payments_raw"

# Consumer settings
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "orders-payments-joiner-v2")
