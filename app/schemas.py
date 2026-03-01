from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EventIn(BaseModel):
    timestamp: datetime
    worker_id: Optional[str]
    workstation_id: Optional[str]
    event_type: str
    confidence: Optional[float]
    count: Optional[int] = 0


class EventOut(EventIn):
    id: int


class WorkerSchema(BaseModel):
    worker_id: str
    name: str


class WorkstationSchema(BaseModel):
    station_id: str
    name: str
