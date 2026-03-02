# AI-Powered Worker Productivity Dashboard

A production-style full-stack application that ingests AI-generated worker activity events from CCTV systems and computes real-time productivity metrics across workers, workstations, and the entire factory.

Live Deployment:
https://ai-powered-worker-productivity-dashboard-d8nb.onrender.com/

---

## 1. Architecture Overview

### Edge → Backend → Dashboard Flow

```
AI Cameras (Edge)
        ↓
Structured JSON Events
        ↓
POST /events
        ↓
FastAPI Backend
        ↓
SQLite Database (events.db)
        ↓
Metrics Engine (Dynamic Aggregation)
        ↓
GET /metrics
        ↓
Frontend Dashboard (static/index.html)
```

### Stack Used

- Backend: FastAPI
- Database: SQLite (SQLAlchemy ORM)
- Frontend: HTML + JavaScript
- Deployment: Render Web Service
- Containerization: Docker

The backend serves both APIs and the static dashboard.

---

## 2. Database Schema

Three core tables:

### Workers
- worker_id (Primary Key)
- name

### Workstations
- station_id (Primary Key)
- name

### Events
- id (Primary Key)
- timestamp (datetime)
- worker_id (Foreign Key)
- workstation_id (Foreign Key)
- event_type (working | idle | absent | product_count)
- confidence (float)
- count (int, used for product_count)

Duplicate events are prevented using a unique constraint on:
(timestamp, worker_id, workstation_id, event_type, count)

All events are persisted permanently in SQLite.

---

## 3. API Endpoints

### Ingest AI Event
POST /events

Example:
{
  "timestamp": "2026-01-15T10:15:00Z",
  "worker_id": "W1",
  "workstation_id": "S3",
  "event_type": "working",
  "confidence": 0.93,
  "count": 1
}

Duplicate events are gracefully ignored.

---

### Fetch Metrics
GET /metrics

Returns factory-level, worker-level, and workstation-level metrics.

---

### List Workers
GET /workers

### List Workstations
GET /workstations

---

### Seed Data
POST /seed

Clears existing data and regenerates a simulated 8-hour shift.

This allows evaluators to refresh dummy data without modifying code or database manually.

---

## 4. Metric Definitions & Assumptions

### Time-Based Computation Model

Events are sorted chronologically per worker.

Duration between two consecutive events is calculated as:

duration = next.timestamp - current.timestamp

Time is converted to hours.

---

### Worker-Level Metrics

Active Time:
Sum of durations where event_type = "working"

Idle Time:
Sum of durations where event_type = "idle"

Utilization %:
active_time / (active_time + idle_time) × 100

Total Units Produced:
Sum of count where event_type = "product_count"

Units per Hour:
total_units / active_time

---

### Workstation-Level Metrics

Occupancy Time:
Sum of working durations for that station

Utilization %:
occupancy_time / total_observed_time

Total Units Produced:
Sum of product_count events at that station

Throughput Rate:
total_units / occupancy_time

---

### Factory-Level Metrics

Total Productive Time:
Sum of active time across all workers

Total Production Count:
Sum of all product_count events

Average Production Rate:
Average of worker production rates

Average Utilization:
Average of worker utilization %

---

### Assumptions

- Time between consecutive events defines activity duration
- Events may arrive out-of-order; they are sorted before aggregation
- Product_count events represent discrete production increments
- Metrics are dynamically computed on every request (no caching)

---

## 5. Frontend Dashboard

The dashboard displays:

- Factory-level summary metrics
- Worker metrics table (6 workers)
- Workstation metrics table (6 stations)
- Worker & station filters
- Reseed button
- Generate Event button

The UI is intentionally minimal but structured and functional.

---

## 6. Handling Edge Cases

### Intermittent Connectivity

In production:
- Edge devices would buffer events locally
- Retry with exponential backoff
- Backend supports idempotent inserts

---

### Duplicate Events

Handled using database-level unique constraint.

If duplicate insertion is attempted:
- Transaction rolls back
- Duplicate is ignored safely

---

### Out-of-Order Timestamps

Events are sorted chronologically before computing durations.

This ensures accurate time-based calculations even if events arrive late.

---

## 7. Model Versioning Strategy

To support future ML model updates:

- Add model_version column to events
- Store version with each AI-generated event
- Compare production metrics across model versions
- Roll back if performance degrades

---

## 8. Model Drift Detection

Potential strategy:

- Monitor confidence distribution shifts
- Track drop in production rate
- Use statistical tests (KS-test, PSI)
- Alert if utilization deviates beyond threshold

---

## 9. Scaling Strategy

### From 5 Cameras → 100+ Cameras

- Introduce message queue (Kafka / RabbitMQ)
- Separate ingestion service
- Horizontal scaling of API layer
- Use PostgreSQL instead of SQLite

---

### Multi-Site Deployment

- Separate DB per factory
- Central aggregation service
- Cloud object storage for raw logs
- Multi-tenant architecture

---

## 10. Containerization

Dockerized for consistent deployment.

Run locally:

docker build -t worker-dashboard .
docker run -p 8000:8000 worker-dashboard

Access:
http://localhost:8000/

---

## 11. Deployment

Hosted on Render as a Web Service.

Root URL serves dashboard:
https://ai-powered-worker-productivity-dashboard-d8nb.onrender.com/

Swagger Docs:
https://ai-powered-worker-productivity-dashboard-d8nb.onrender.com/docs

---

## 12. Tradeoffs

- SQLite chosen for simplicity (single-node use case)
- Metrics computed dynamically (no caching layer)
- No authentication layer (assignment scope)
- No async event streaming (kept simple for evaluation)

---

## 13. Summary

This project demonstrates:

- Event-driven metric computation
- Production-style API design
- Database schema modeling
- Handling of real-world edge cases
- Containerized deployment
- System scalability planning

The system mimics how AI-based factory monitoring solutions would aggregate and expose productivity insights in real-world environments.
