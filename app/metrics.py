from sqlalchemy.orm import Session
from . import models
from datetime import datetime
from collections import defaultdict


def _get_worker_state_events(session: Session):
    # return events that represent state changes (working/idle/absent) per worker
    q = session.query(models.Event).filter(models.Event.event_type.in_(["working", "idle", "absent"]))
    events = q.order_by(models.Event.worker_id, models.Event.timestamp).all()
    return events


def compute_worker_metrics(session: Session):
    workers = {w.worker_id: w.name for w in session.query(models.Worker).all()}
    # initialize metrics
    metrics = {wid: {"total_active_time": 0.0, "total_idle_time": 0.0, "units_produced": 0, "utilization": 0.0} for wid in workers.keys()}

    # process state events grouped by worker
    state_events = _get_worker_state_events(session)
    grouped = defaultdict(list)
    for e in state_events:
        if e.worker_id:
            grouped[e.worker_id].append(e)

    for wid, evs in grouped.items():
        evs_sorted = sorted(evs, key=lambda x: x.timestamp)
        for i in range(len(evs_sorted)-1):
            cur = evs_sorted[i]
            nxt = evs_sorted[i+1]
            duration = (nxt.timestamp - cur.timestamp).total_seconds() / 3600.0
            if cur.event_type == 'working':
                metrics[wid]['total_active_time'] += duration
            elif cur.event_type == 'idle':
                metrics[wid]['total_idle_time'] += duration
        # no assumption after last event

    # production counts per worker
    prod_q = session.query(models.Event).filter(models.Event.event_type == 'product_count')
    for e in prod_q.all():
        if e.worker_id:
            metrics[e.worker_id]['units_produced'] += (e.count or 0)

    # compute utilization = active / (active + idle) if denominator >0
    for wid, m in metrics.items():
        denom = m['total_active_time'] + m['total_idle_time']
        m['utilization'] = (m['total_active_time'] / denom * 100.0) if denom > 0 else 0.0
        m['units_per_hour'] = (m['units_produced'] / m['total_active_time']) if m['total_active_time'] > 0 else 0.0

    # attach names
    for wid in metrics.keys():
        metrics[wid]['name'] = workers.get(wid)

    return metrics


def compute_workstation_metrics(session: Session):
    stations = {s.station_id: s.name for s in session.query(models.Workstation).all()}
    metrics = {sid: {'occupancy_time': 0.0, 'units_produced': 0, 'utilization': 0.0} for sid in stations.keys()}

    # occupancy based on worker state events with workstation_id
    q = session.query(models.Event).filter(models.Event.event_type.in_(['working','idle']))
    events = q.order_by(models.Event.workstation_id, models.Event.timestamp).all()
    grouped = defaultdict(list)
    for e in events:
        if e.workstation_id:
            grouped[e.workstation_id].append(e)

    for sid, evs in grouped.items():
        evs_sorted = sorted(evs, key=lambda x: x.timestamp)
        for i in range(len(evs_sorted)-1):
            cur = evs_sorted[i]
            nxt = evs_sorted[i+1]
            duration = (nxt.timestamp - cur.timestamp).total_seconds() / 3600.0
            if cur.event_type == 'working':
                metrics[sid]['occupancy_time'] += duration
            # idle doesn't add occupancy

    # production per station
    prod_q = session.query(models.Event).filter(models.Event.event_type == 'product_count')
    for e in prod_q.all():
        if e.workstation_id:
            metrics[e.workstation_id]['units_produced'] += (e.count or 0)

    # compute utilization: occupancy / (occupancy + idle_time_at_station) approximate (we lack idle_by_station)
    # For simplicity, assume utilization = occupancy_time / total_hours_observed where total_hours_observed = max timestamp - min timestamp across events
    all_ts = [e.timestamp for e in session.query(models.Event).order_by(models.Event.timestamp).all()]
    if all_ts:
        total_hours = (max(all_ts) - min(all_ts)).total_seconds() / 3600.0
    else:
        total_hours = 0.0

    for sid, m in metrics.items():
        m['utilization'] = (m['occupancy_time'] / total_hours * 100.0) if total_hours > 0 else 0.0
        m['throughput'] = (m['units_produced'] / total_hours) if total_hours > 0 else 0.0
        m['name'] = stations.get(sid)

    return metrics


def compute_factory_metrics(session: Session):
    worker_metrics = compute_worker_metrics(session)
    station_metrics = compute_workstation_metrics(session)

    total_productive_time = sum([m['total_active_time'] for m in worker_metrics.values()])
    total_production = sum([m['units_produced'] for m in worker_metrics.values()])
    avg_prod_rate = 0.0
    total_hours = 0.0
    all_ts = [e.timestamp for e in session.query(models.Event).order_by(models.Event.timestamp).all()]
    if all_ts:
        total_hours = (max(all_ts) - min(all_ts)).total_seconds() / 3600.0
    if total_hours > 0:
        avg_prod_rate = total_production / total_hours

    avg_util = 0.0
    if worker_metrics:
        avg_util = sum([m['utilization'] for m in worker_metrics.values()]) / len(worker_metrics)

    return {
        'total_productive_time': total_productive_time,
        'total_production': total_production,
        'avg_production_rate': avg_prod_rate,
        'avg_worker_utilization': avg_util,
        'worker_metrics': worker_metrics,
        'station_metrics': station_metrics,
    }
