"""
FastAPI backend for the real-time analytics dashboard.
Serves stats, recent joined events, and SSE stream. Runs the Kafka join consumer in a background thread.
"""
from __future__ import annotations

import asyncio
import json
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.consumer import kafka_consumer
from backend import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load config (trigger .env)
    from backend.consumer import config as _cfg  # noqa: F401

    stop = threading.Event()
    thread = threading.Thread(
        target=kafka_consumer.run_consumer,
        kwargs={
            "on_joined": store.record_joined,
            "on_order": store.record_order,
            "on_payment": store.record_payment,
            "stop_event": stop,
        },
        daemon=True,
    )
    thread.start()
    yield
    stop.set()
    thread.join(timeout=10.0)


app = FastAPI(title="Real-time Analytics API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats")
def stats():
    return store.get_stats()


@app.get("/api/recent")
def recent(limit: int = 50):
    return {"events": store.get_recent(min(limit, 100))}


@app.get("/api/events")
async def events():
    """Server-Sent Events stream of joined events."""

    async def gen():
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        store.add_sse_queue(q, loop)
        try:
            while True:
                try:
                    evt = await asyncio.wait_for(q.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield ":\n\n"
                    continue
                yield f"data: {json.dumps(evt, default=str)}\n\n"
        finally:
            store.remove_sse_queue(q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
