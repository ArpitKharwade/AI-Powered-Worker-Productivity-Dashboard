# from fastapi import FastAPI, HTTPException, Depends
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy.orm import Session
# from . import db, models, schemas, metrics
# from datetime import datetime, timedelta
# from typing import List

# app = FastAPI(title="AI Worker Productivity Dashboard")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.mount("/static", StaticFiles(directory="./static"), name="static")


# def get_db():
#     db_session = db.SessionLocal()
#     try:
#         yield db_session
#     finally:
#         db_session.close()


# @app.on_event("startup")
# def startup():
#     db.init_db()
#     # auto-seed if empty
#     session = db.SessionLocal()
#     try:
#         wcount = session.query(models.Worker).count()
#         if wcount == 0:
#             # reuse seed logic from endpoint
#             session.query(models.Event).delete()
#             session.query(models.Worker).delete()
#             session.query(models.Workstation).delete()
#             session.commit()
#             workers = [(f"W{i}", f"Worker {i}") for i in range(1,7)]
#             stations = [(f"S{i}", f"Station {i}") for i in range(1,7)]
#             for wid, name in workers:
#                 session.add(models.Worker(worker_id=wid, name=name))
#             for sid, name in stations:
#                 session.add(models.Workstation(station_id=sid, name=name))
#             session.commit()
#             from datetime import datetime, timedelta
#             start = datetime.utcnow() - timedelta(hours=8)
#             for i, (wid, _) in enumerate(workers):
#                 sid = stations[i][0]
#                 t = start
#                 for k in range(16):
#                     etype = 'working' if k % 2 == 0 else 'idle'
#                     session.add(models.Event(timestamp=t, worker_id=wid, workstation_id=sid, event_type=etype, confidence=0.9, count=0))
#                     if etype == 'working':
#                         session.add(models.Event(timestamp=t + timedelta(minutes=10), worker_id=wid, workstation_id=sid, event_type='product_count', confidence=0.99, count=5))
#                     t = t + timedelta(minutes=30)
#             session.commit()
#     finally:
#         session.close()


# @app.post("/events", status_code=201)
# def ingest_event(e: schemas.EventIn, session: Session = Depends(get_db)):
#     # dedupe by unique constraint; if duplicate, ignore
#     ev = models.Event(timestamp=e.timestamp, worker_id=e.worker_id, workstation_id=e.workstation_id, event_type=e.event_type, confidence=e.confidence, count=e.count)
#     try:
#         session.add(ev)
#         session.commit()
#         session.refresh(ev)
#     except Exception:
#         session.rollback()
#         raise HTTPException(status_code=400, detail="Duplicate or invalid event")
#     return {"status": "ok", "id": ev.id}


# @app.get("/workers")
# def list_workers(session: Session = Depends(get_db)):
#     ws = session.query(models.Worker).all()
#     return [{"worker_id": w.worker_id, "name": w.name} for w in ws]


# @app.get("/workstations")
# def list_stations(session: Session = Depends(get_db)):
#     ss = session.query(models.Workstation).all()
#     return [{"station_id": s.station_id, "name": s.name} for s in ss]


# @app.post("/seed")
# def seed_data(session: Session = Depends(get_db)):
#     # Clear tables
#     session.query(models.Event).delete()
#     session.query(models.Worker).delete()
#     session.query(models.Workstation).delete()
#     session.commit()

#     # create 6 workers and 6 stations
#     workers = [(f"W{i}", f"Worker {i}") for i in range(1,7)]
#     stations = [(f"S{i}", f"Station {i}") for i in range(1,7)]
#     for wid, name in workers:
#         session.add(models.Worker(worker_id=wid, name=name))
#     for sid, name in stations:
#         session.add(models.Workstation(station_id=sid, name=name))
#     session.commit()

#     # generate events across a simulated 8-hour shift
#     start = datetime.utcnow() - timedelta(hours=8)
#     # for each worker, alternate working and idle every 30 minutes and emit product_count occasionally
#     for i, (wid, _) in enumerate(workers):
#         sid = stations[i][0]
#         t = start
#         for k in range(16):
#             # alternate
#             etype = 'working' if k % 2 == 0 else 'idle'
#             session.add(models.Event(timestamp=t, worker_id=wid, workstation_id=sid, event_type=etype, confidence=0.9, count=0))
#             # occasional production event during working
#             if etype == 'working':
#                 session.add(models.Event(timestamp=t + timedelta(minutes=10), worker_id=wid, workstation_id=sid, event_type='product_count', confidence=0.99, count=5))
#             t = t + timedelta(minutes=30)

#     session.commit()
#     return {"status": "seeded"}


# @app.get("/metrics")
# def get_metrics(session: Session = Depends(get_db)):
#     m = metrics.compute_factory_metrics(session)
#     return m


# @app.get("/")
# def root():
#     return {"message": "Visit /static/index.html for dashboard"}







#new main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import db, models, schemas, metrics
from datetime import datetime, timedelta

app = FastAPI(title="AI Worker Productivity Dashboard")

# ------------------- CORS -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Serve Frontend at Root -------------------
# This makes "/" automatically serve static/index.html
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ------------------- DB Dependency -------------------
def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


# ------------------- Startup: Init + Auto Seed -------------------
@app.on_event("startup")
def startup():
    db.init_db()

    session = db.SessionLocal()
    try:
        if session.query(models.Worker).count() == 0:
            session.query(models.Event).delete()
            session.query(models.Worker).delete()
            session.query(models.Workstation).delete()
            session.commit()

            workers = [(f"W{i}", f"Worker {i}") for i in range(1, 7)]
            stations = [(f"S{i}", f"Station {i}") for i in range(1, 7)]

            for wid, name in workers:
                session.add(models.Worker(worker_id=wid, name=name))

            for sid, name in stations:
                session.add(models.Workstation(station_id=sid, name=name))

            session.commit()

            start = datetime.utcnow() - timedelta(hours=8)

            for i, (wid, _) in enumerate(workers):
                sid = stations[i][0]
                t = start

                for k in range(16):
                    etype = "working" if k % 2 == 0 else "idle"

                    session.add(models.Event(
                        timestamp=t,
                        worker_id=wid,
                        workstation_id=sid,
                        event_type=etype,
                        confidence=0.9,
                        count=0
                    ))

                    if etype == "working":
                        session.add(models.Event(
                            timestamp=t + timedelta(minutes=10),
                            worker_id=wid,
                            workstation_id=sid,
                            event_type="product_count",
                            confidence=0.99,
                            count=5
                        ))

                    t = t + timedelta(minutes=30)

            session.commit()

    finally:
        session.close()


# ------------------- Ingest Events -------------------
@app.post("/events", status_code=201)
def ingest_event(e: schemas.EventIn, session: Session = Depends(get_db)):
    ev = models.Event(
        timestamp=e.timestamp,
        worker_id=e.worker_id,
        workstation_id=e.workstation_id,
        event_type=e.event_type,
        confidence=e.confidence,
        count=e.count
    )

    try:
        session.add(ev)
        session.commit()
        session.refresh(ev)
    except Exception:
        session.rollback()
        return {"status": "duplicate ignored"}

    return {"status": "ok", "id": ev.id}


# ------------------- Workers -------------------
@app.get("/workers")
def list_workers(session: Session = Depends(get_db)):
    ws = session.query(models.Worker).all()
    return [{"worker_id": w.worker_id, "name": w.name} for w in ws]


# ------------------- Workstations -------------------
@app.get("/workstations")
def list_stations(session: Session = Depends(get_db)):
    ss = session.query(models.Workstation).all()
    return [{"station_id": s.station_id, "name": s.name} for s in ss]


# ------------------- Manual Seed -------------------
@app.post("/seed")
def seed_data(session: Session = Depends(get_db)):
    session.query(models.Event).delete()
    session.query(models.Worker).delete()
    session.query(models.Workstation).delete()
    session.commit()

    workers = [(f"W{i}", f"Worker {i}") for i in range(1, 7)]
    stations = [(f"S{i}", f"Station {i}") for i in range(1, 7)]

    for wid, name in workers:
        session.add(models.Worker(worker_id=wid, name=name))

    for sid, name in stations:
        session.add(models.Workstation(station_id=sid, name=name))

    session.commit()

    start = datetime.utcnow() - timedelta(hours=8)

    for i, (wid, _) in enumerate(workers):
        sid = stations[i][0]
        t = start

        for k in range(16):
            etype = "working" if k % 2 == 0 else "idle"

            session.add(models.Event(
                timestamp=t,
                worker_id=wid,
                workstation_id=sid,
                event_type=etype,
                confidence=0.9,
                count=0
            ))

            if etype == "working":
                session.add(models.Event(
                    timestamp=t + timedelta(minutes=10),
                    worker_id=wid,
                    workstation_id=sid,
                    event_type="product_count",
                    confidence=0.99,
                    count=5
                ))

            t = t + timedelta(minutes=30)

    session.commit()
    return {"status": "seeded"}


# ------------------- Metrics -------------------
@app.get("/metrics")
def get_metrics(session: Session = Depends(get_db)):
    return metrics.compute_factory_metrics(session)