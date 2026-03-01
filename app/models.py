from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base
import datetime


class Worker(Base):
    __tablename__ = "workers"
    worker_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)


class Workstation(Base):
    __tablename__ = "workstations"
    station_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    worker_id = Column(String, ForeignKey("workers.worker_id"), nullable=True)
    workstation_id = Column(String, ForeignKey("workstations.station_id"), nullable=True)
    event_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    count = Column(Integer, nullable=True, default=0)
    raw_hash = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('timestamp', 'worker_id', 'workstation_id', 'event_type', 'count', name='uix_event_unique'),
    )
