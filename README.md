# Real-time Analytics Dashboard

Stream **orders** and **payments** to Kafka, join them in a consumer, and view live stats + joined events in a React dashboard.

## Architecture

```
Producer (orders_raw, payments_raw)  →  Confluent Kafka
                                              ↓
Backend (FastAPI + join consumer)    ←  orders_raw, payments_raw
       ↓
   /api/stats, /api/events (SSE)
       ↓
Frontend (React + Vite)  →  Dashboard (stats + live table)
```

- **Producer**: Reads Olist CSVs, publishes orders and payments to `orders_raw` and `payments_raw` (keyed by `order_id`).
- **Backend**: Runs a Kafka join consumer (orders × payments on `order_id`), exposes REST + SSE.
- **Frontend**: Polls `/api/stats`, subscribes to `/api/events` (SSE) for live joined events.

## Prerequisites

- **Python 3.11+** (producer, backend)
- **Node.js 18+** (frontend)
- **Confluent Cloud** (or local Kafka) with `BOOTSTRAP_SERVERS`, `API_KEY`, `API_SECRET` in `.env` at project root.

## Setup

### 1. Environment

Create a `.env` in the **project root**:

```
BOOTSTRAP_SERVERS="pkc-xxxx.region.aws.confluent.cloud:9092"
API_KEY="your-api-key"
API_SECRET="your-api-secret"
```

Optional: `KAFKA_GROUP_ID` (default: `orders-payments-joiner`).

### 2. Backend deps

From project root:

```bash
pip install -r backend/requirements.txt
```

(Or use a venv and install there.)

### 3. Producer deps

```bash
cd producer
pip install -r requirements.txt
cd ..
```

### 4. Frontend deps

```bash
cd frontend
npm install
cd ..
```

## How to run

Use **three terminals** (all from project root unless specified).

### Terminal 1: Backend (FastAPI + Kafka consumer)

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Or:

```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`
- Stats: `http://localhost:8000/api/stats`
- SSE: `http://localhost:8000/api/events`

### Terminal 2: Producer

```bash
cd producer
python producer.py
```

Keep it running to stream orders and payments to Kafka.

### Terminal 3: Frontend

```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173**. The dashboard shows:

- **Stats**: orders seen, payments seen, joined events count.
- **Joined events table**: recent order+payment joins (live via SSE when producer is running).

## Run consumer standalone (no backend)

To run only the join consumer with print output:

```bash
python -m backend.consumer.kafka_consumer
```

## Project layout

```
├── .env                    # Kafka credentials (project root)
├── backend/
│   ├── app.py              # FastAPI app, SSE, stats
│   ├── store.py            # In-memory store for joined events
│   ├── consumer/
│   │   ├── config.py       # Kafka config, loads .env
│   │   └── kafka_consumer.py
│   └── requirements.txt
├── producer/
│   ├── producer.py
│   ├── config.py
│   ├── data/               # Olist CSVs
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── App.css
    ├── package.json
    └── vite.config.js      # Proxy /api → backend
```

## Notes

- Create Kafka topics `orders_raw` and `payments_raw` (e.g. in Confluent Cloud) before running the producer.
- The frontend proxies `/api` to the backend (see `frontend/vite.config.js`) when using `npm run dev`.
