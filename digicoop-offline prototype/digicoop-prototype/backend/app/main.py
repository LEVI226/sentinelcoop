"""
API centrale — CIF DigiCoop-WA+, Thématique 01 (Filtrage LBC/FT/FP).

Deux routes portent toute la synchronisation offline-first :
  POST /sync/push  — le terminal pousse ses écritures locales (upsert idempotent)
  GET  /sync/pull   — le terminal récupère le delta des listes de sanctions/PPE

Le reste (health, alerts) sert au dashboard conformité et à la sentinelle
réseau du terminal (voir frontend/src/sync/connectivitySentinel.js).
"""
import datetime as dt
import uuid as uuidlib

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select

from .database import Base, engine, get_db
from . import models, schemas, crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CIF DigiCoop-WA+ — Central de conformité (Thématique 01)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre à l'origine du terminal en production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Utilisé par la sentinelle réseau du terminal — doit répondre vite et sans état."""
    return {"status": "ok", "time": dt.datetime.utcnow().isoformat()}


@app.post("/sync/push", response_model=schemas.PushResponse)
def push(req: schemas.PushRequest, db: Session = Depends(get_db)):
    results = []
    for item in req.items:
        upsert_fn = crud.UPSERTERS.get(item.entity_type)
        if upsert_fn is None:
            results.append(schemas.PushResultItem(uuid=item.uuid, status="error", detail="type d'entité inconnu"))
            continue
        try:
            upsert_fn(db, item.uuid, item.agency_id, item.payload)
            db.add(models.SyncLog(
                id=str(uuidlib.uuid4()),
                agency_id=item.agency_id,
                entity_type=item.entity_type,
                entity_id=item.uuid,
                direction="push",
                status="ok",
            ))
            db.commit()
            results.append(schemas.PushResultItem(uuid=item.uuid, status="synced"))
        except Exception as exc:  # noqa: BLE001 — on veut renvoyer l'erreur au terminal, pas planter le lot entier
            db.rollback()
            db.add(models.SyncLog(
                id=str(uuidlib.uuid4()),
                agency_id=item.agency_id,
                entity_type=item.entity_type,
                entity_id=item.uuid,
                direction="push",
                status="error",
                detail=str(exc),
            ))
            db.commit()
            results.append(schemas.PushResultItem(uuid=item.uuid, status="error", detail=str(exc)))
    return schemas.PushResponse(results=results, server_time=dt.datetime.utcnow().isoformat())


@app.get("/sync/pull", response_model=schemas.PullResponse)
def pull(since: str = "1970-01-01T00:00:00", db: Session = Depends(get_db)):
    try:
        since_dt = dt.datetime.fromisoformat(since)
    except ValueError:
        raise HTTPException(status_code=400, detail="paramètre 'since' invalide (ISO 8601 attendu)")

    rows = db.execute(
        select(models.WatchlistEntry).where(models.WatchlistEntry.updated_at > since_dt)
    ).scalars().all()

    watchlist = [
        schemas.WatchlistEntryOut(
            id=r.id, full_name=r.full_name, category=r.category,
            source=r.source, updated_at=r.updated_at.isoformat(),
        ) for r in rows
    ]
    return schemas.PullResponse(watchlist=watchlist, server_time=dt.datetime.utcnow().isoformat())


@app.get("/alerts", response_model=list[schemas.AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    """Alimente le dashboard conformité — étape 6 du parcours de contrôle."""
    rows = db.execute(select(models.Alert).order_by(models.Alert.created_at.desc())).scalars().all()
    return [
        schemas.AlertOut(
            id=r.id, client_id=r.client_id, matched_name=r.matched_name,
            match_score=r.match_score, severity=r.severity, decision=r.decision,
            created_at=r.created_at.isoformat(),
        ) for r in rows
    ]


@app.post("/alerts/{alert_id}/decision")
def decide_alert(alert_id: str, body: schemas.DecisionRequest, db: Session = Depends(get_db)):
    """Décision humaine — dernière étape du parcours de contrôle, journalisée."""
    obj = db.get(models.Alert, alert_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="alerte introuvable")
    obj.decision = body.decision
    db.add(models.SyncLog(
        id=str(uuidlib.uuid4()), agency_id=obj.agency_id, entity_type="alert",
        entity_id=alert_id, direction="push", status="ok", detail=f"décision : {body.decision}",
    ))
    db.commit()
    return {"id": obj.id, "decision": obj.decision}
