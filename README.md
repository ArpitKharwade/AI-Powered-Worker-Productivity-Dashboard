# AI-Powered Worker Productivity Dashboard

This repository contains a small production-style web application that ingests AI-generated events from CCTV CV systems, stores them, computes productivity metrics, and displays them in a dashboard.

Run locally (development):

1. Create a Python environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the app:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Seed sample data (or use the dashboard button):

```powershell
curl -X POST http://localhost:8000/seed
```

4. Open dashboard at: http://localhost:8000/static/index.html — the dashboard includes:
  - Filters for worker and workstation
  - A "Reseed Data" button to repopulate dummy data
  - A "Generate Event" button to push a random working/product_count event
  - Clickable worker/station rows to view a details panel and send a quick product_count event

Docker:

```powershell
docker build -t ai-dashboard .
docker run -p 8000:8000 ai-dashboard
```

Architecture
- Backend: FastAPI + SQLite (SQLAlchemy)
- Frontend: simple static HTML/JS served by FastAPI
- DB: SQLite persisted to `events.db`

Database Schema
- `workers` (worker_id PK, name)
- `workstations` (station_id PK, name)
- `events` (id PK, timestamp, worker_id FK, workstation_id FK, event_type, confidence, count)

Metric definitions & assumptions
- Worker-level:
  - Total active time: sum of durations between "working" events and the next state event (hours).
  - Total idle time: sum of durations between "idle" events and the next state event (hours).
  - Utilization %: active / (active + idle).
  - Total units produced: sum of `product_count` events' `count` for the worker.
  - Units per hour: units_produced / total_active_time.
- Workstation-level:
  - Occupancy time: sum of durations where workstation had `working` events.
  - Utilization %: occupancy_time / observed_time_window.
  - Throughput: units produced / observed_time_window.
- Factory-level:
  - Total productive time: sum of worker total_active_time.
  - Total production count: sum of worker units_produced.
  - Average production rate: total_production / observed_time_window.
  - Average utilization: mean of worker utilizations.

Event handling assumptions
- Intermittent connectivity: clients can buffer and retry; backend dedupes exact-duplicate events via an application-unique constraint; ingestion is idempotent for identical events.
- Duplicate events: insert uses a unique index on (timestamp, worker_id, workstation_id, event_type, count); duplicates return 400 and are ignored by clients.
- Out-of-order timestamps: metrics computation sorts events by timestamp before computing durations; this handles re-ordered arrivals.

How to extend for model/versioning, drift, and scale
- Model versioning: include `model_version` field in events; store metadata; add endpoints to query by version and track metrics per version.
- Detect model drift: compute distributions of confidence and event rates over time; alert when distributions shift beyond thresholds (e.g., KL divergence, population stability index).
- Trigger retraining: schedule retraining when drift thresholds exceeded or when labels become available; use a CI/CD pipeline to train, validate and promote model versions.

Scaling from 5 → 100+ cameras → multi-site
- Move from SQLite → Postgres for concurrency and size.
- Use batching and message queues (Kafka, SQS) at ingestion to handle bursty input.
- Shard events by site/camera and aggregate metrics via worker/job runners or stream processors (Flink, ksqlDB).
- Add caching and precomputed aggregates (daily/hourly) for dashboard performance.
