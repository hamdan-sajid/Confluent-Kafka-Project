"""
Orders–payments join consumer. Consumes from orders_raw and payments_raw,
joins on order_id, and emits (order + payment) via on_joined callback.

Run standalone: python -m backend.consumer.kafka_consumer
Or run inside FastAPI backend (consumer thread).
"""
from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from typing import Callable

from confluent_kafka import Consumer, KafkaException

from backend.consumer import config as cfg

API_KEY = cfg.API_KEY
API_SECRET = cfg.API_SECRET
BOOTSTRAP_SERVERS = cfg.BOOTSTRAP_SERVERS
GROUP_ID = cfg.GROUP_ID
ORDERS_TOPIC = cfg.ORDERS_TOPIC
PAYMENTS_TOPIC = cfg.PAYMENTS_TOPIC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _process_message(
    topic: str,
    key: str | None,
    value: dict,
    on_joined: Callable[[dict], None],
    *,
    _orders: dict,
    _payments: dict,
    on_order: Callable[[dict], None] | None = None,
    on_payment: Callable[[dict], None] | None = None,
) -> None:
    if key is None:
        print("  [SKIP] null key from topic=%s" % topic)
        logger.warning("skipping message with null key from %s", topic)
        return

    if topic == ORDERS_TOPIC:
        print("  [ORDER]  key=%s order_status=%s" % (key, value.get("order_status", "?")))
        if on_order:
            on_order(value)
        _orders[key] = value
        while _payments[key]:
            payment = _payments[key].pop(0)
            joined = {**_orders[key], **payment}
            print("  [JOINED] key=%s payment_value=%s" % (key, joined.get("payment_value", "?")))
            on_joined(joined)
        return

    if topic == PAYMENTS_TOPIC:
        print("  [PAYMENT] key=%s payment_type=%s payment_value=%s" % (key, value.get("payment_type", "?"), value.get("payment_value", "?")))
        if on_payment:
            on_payment(value)
        _payments[key].append(value)
        if key not in _orders:
            return
        payment = _payments[key].pop()
        joined = {**_orders[key], **payment}
        print("  [JOINED] key=%s payment_value=%s" % (key, joined.get("payment_value", "?")))
        on_joined(joined)


def run_consumer(
    *,
    on_joined: Callable[[dict], None],
    on_order: Callable[[dict], None] | None = None,
    on_payment: Callable[[dict], None] | None = None,
    stop_event: threading.Event | None = None,
) -> None:
    """Run the join consumer. Exits when stop_event is set (if provided)."""
    missing = [
        k
        for k, v in (
            ("BOOTSTRAP_SERVERS", BOOTSTRAP_SERVERS),
            ("API_KEY", API_KEY),
            ("API_SECRET", API_SECRET),
        )
        if not v
    ]
    if missing:
        raise SystemExit(f"Missing required env vars: {missing}. Set them in .env or environment.")

    conf = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": API_KEY,
        "sasl.password": API_SECRET,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "session.timeout.ms": 30000,
        "socket.connection.setup.timeout.ms": 30000,
    }
    debug = os.environ.get("KAFKA_DEBUG")
    if debug:
        conf["debug"] = str(debug)
    consumer = None
    try:
        consumer = Consumer(conf)
        consumer.subscribe([ORDERS_TOPIC, PAYMENTS_TOPIC])
        _orders: dict[str, dict] = {}
        _payments: dict[str, list[dict]] = defaultdict(list)
        _first_message = True
        logger.info("Join consumer started (orders_raw + payments_raw, group=%s)", GROUP_ID)
        print("Join consumer started (group=%s). Waiting for messages..." % GROUP_ID)
        print("  To read from START of topics, use a NEW group: set env KAFKA_GROUP_ID=orders-joiner-v2")
        while stop_event is None or not stop_event.is_set():
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            if _first_message:
                _first_message = False
                print("  First message received: %s [p=%s o=%s]" % (msg.topic(), msg.partition(), msg.offset()))
            key = msg.key().decode("utf-8") if msg.key() else None
            print("  << msg topic=%s key=%s partition=%s offset=%s" % (msg.topic(), key, msg.partition(), msg.offset()))
            raw = msg.value()
            if raw is None:
                print("  [SKIP] null value from topic=%s" % msg.topic())
                logger.warning("skipping message with null value from %s", msg.topic())
                continue
            try:
                value = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print("  [SKIP] invalid JSON from topic=%s: %s" % (msg.topic(), e))
                logger.warning("invalid message value from %s: %s", msg.topic(), e)
                continue
            _process_message(
                msg.topic(),
                key,
                value,
                on_joined,
                _orders=_orders,
                _payments=_payments,
                on_order=on_order,
                on_payment=on_payment,
            )
    except Exception as e:
        logger.exception("Consumer error: %s", e)
    finally:
        if consumer:
            consumer.close()
        print("Consumer closed.")
        logger.info("Consumer closed")


def _default_on_joined(joined: dict) -> None:
    logger.info(
        "joined order_id=%s payment_value=%s",
        joined.get("order_id"),
        joined.get("payment_value"),
    )
    print(
        "✅ JOINED",
        joined.get("order_id"),
        "| payment_value:",
        joined.get("payment_value"),
        "|",
        json.dumps(joined, default=str)[:120],
    )


def run() -> None:
    """Run consumer standalone with print-friendly callback."""
    run_consumer(on_joined=_default_on_joined, stop_event=None)


if __name__ == "__main__":
    run()
