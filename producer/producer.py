import json
import time
import pandas as pd
from confluent_kafka import Producer
from config import BOOTSTRAP_SERVERS, API_KEY, API_SECRET, ORDERS_TOPIC, PAYMENTS_TOPIC, STREAM_INTERVAL

# Kafka configuration for Confluent Cloud
conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": API_KEY,
    "sasl.password": API_SECRET,
    "acks": "all"
}

producer = Producer(conf)

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Sent to {msg.topic()} [{msg.partition()}]")

# Load CSV data and join so we send matching order+payment pairs (same order_id)
df_orders = pd.read_csv("data/olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
df_payments = pd.read_csv("data/olist_order_payments_dataset.csv")
# Inner join: each row = one order + one payment with the same order_id
merged = df_orders.merge(df_payments, on="order_id", how="inner")
n = len(merged)
print("Starting streaming to Confluent Cloud (matching order+payment pairs)...")
print("  Pairs: %d (same order_id for join)" % n)

i = 0
while True:
    row = merged.iloc[i % n]
    order_id = str(row["order_id"])

    order_event = {
        "order_id": order_id,
        "user_id": str(row["customer_id"]),
        "order_status": row["order_status"],
        "order_purchase_timestamp": row["order_purchase_timestamp"].isoformat(),
    }
    payment_event = {
        "order_id": order_id,
        "payment_type": row["payment_type"],
        "payment_value": float(row["payment_value"]),
    }

    producer.produce(
        topic=ORDERS_TOPIC,
        key=order_id,
        value=json.dumps(order_event),
        callback=delivery_report,
    )
    producer.produce(
        topic=PAYMENTS_TOPIC,
        key=order_id,
        value=json.dumps(payment_event),
        callback=delivery_report,
    )

    producer.poll(0)
    i += 1
    time.sleep(STREAM_INTERVAL)