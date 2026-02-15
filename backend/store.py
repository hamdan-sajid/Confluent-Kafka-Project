"""In-memory store for joined events and stats. Thread-safe."""
from __future__ import annotations

import asyncio
import copy
import threading
from collections import deque
from typing import Any

_orders_seen = 0
_payments_seen = 0
_joined_count = 0
_lock = threading.Lock()
_recent: deque[dict[str, Any]] = deque(maxlen=200)

_sse_queues: list[tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = []
_sse_lock = threading.Lock()


def record_order(_: dict[str, Any]) -> None:
    with _lock:
        global _orders_seen
        _orders_seen += 1


def record_payment(_: dict[str, Any]) -> None:
    with _lock:
        global _payments_seen
        _payments_seen += 1


def record_joined(evt: dict[str, Any]) -> None:
    with _lock:
        global _joined_count
        _joined_count += 1
        _recent.append(copy.deepcopy(evt))

    payload = copy.deepcopy(evt)
    with _sse_lock:
        for q, loop in _sse_queues:
            try:
                loop.call_soon_threadsafe(q.put_nowait, payload)
            except Exception:
                pass


def get_stats() -> dict[str, int | list[dict[str, Any]]]:
    with _lock:
        return {
            "orders_seen": _orders_seen,
            "payments_seen": _payments_seen,
            "joined_count": _joined_count,
            "recent": list(_recent),
        }


def get_recent(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        return list(_recent)[-limit:]


def add_sse_queue(q: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
    with _sse_lock:
        _sse_queues.append((q, loop))


def remove_sse_queue(q: asyncio.Queue) -> None:
    with _sse_lock:
        _sse_queues[:] = [(eq, loop) for eq, loop in _sse_queues if eq is not q]
