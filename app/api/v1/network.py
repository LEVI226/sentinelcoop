"""Module RÉSEAU — CDC §10-11, §26-27 (relations réseau, identité pseudonymisée,
détection de réseaux multiples, risque résiduel)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.customer import Customer, IdentityMatch, NetworkIdentity
from app.models.extra import NetworkRelationship
from app.services.audit_service import audit

router = APIRouter(prefix="/network", tags=["network"])


class RelationshipCreate(BaseModel):
    relation_type: str
    from_type: str
    from_id: int
    to_type: str
    to_id: int
    confidence: float = 1.0


@router.get("/relationships")
async def list_relationships(user: CurrentUser = Depends(require("read:screening")),
                             db: AsyncSession = Depends(get_db),
                             customer_id: int | None = None):
    q = select(NetworkRelationship)
    if customer_id:
        q = q.where((NetworkRelationship.from_id == customer_id)
                    | (NetworkRelationship.to_id == customer_id))
    rows = (await db.execute(q.order_by(NetworkRelationship.type if False else NetworkRelationship.created_at.desc()))).scalars().all()
    return {"success": True, "data": [{
        "id": r.id, "relation_type": r.relation_type,
        "from": {"type": r.from_type, "id": r.from_id},
        "to": {"type": r.to_type, "id": r.to_id},
        "confidence": r.confidence,
        "created_at": r.created_at.isoformat(),
    } for r in rows], "meta": {"requestId": "list"}}


@router.post("/relationships")
async def add_relationship(body: RelationshipCreate, request: Request,
                           user: CurrentUser = Depends(require("manage:screening")),
                           db: AsyncSession = Depends(get_db)):
    r = NetworkRelationship(
        relation_type=body.relation_type, from_type=body.from_type, from_id=body.from_id,
        to_type=body.to_type, to_id=body.to_id, confidence=body.confidence,
    )
    db.add(r)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="RELATIONSHIP_ADDED",
                entity_type="NETWORK", entity_id=r.id,
                new_value={"type": body.relation_type, "from": body.from_id,
                           "to": body.to_id}, request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": r.id}, "meta": {"requestId": request.state.request_id}}


@router.get("/customers/{customer_id}")
async def customer_network(customer_id: int, user: CurrentUser = Depends(require("read:screening")),
                           db: AsyncSession = Depends(get_db)):
    """Graphique réseau d'un client : relations directes + réseaux multiples."""
    res = await db.execute(select(Customer).where(Customer.id == customer_id))
    cust = res.scalar_one_or_none()
    if cust is None:
        raise AppError("CUSTOMER_NOT_FOUND", "Client introuvable", status=404)
    rels = (await db.execute(
        select(NetworkRelationship).where(
            (NetworkRelationship.from_id == customer_id)
            | (NetworkRelationship.to_id == customer_id)))).scalars().all()
    identities = (await db.execute(
        select(IdentityMatch).where(IdentityMatch.customer_id == customer_id))).scalars().all()

    nodes = [{"id": f"C{customer_id}", "label": "ce client", "kind": "CUSTOMER"}]
    edges = []
    for r in rels:
        if r.from_type == "CUSTOMER":
            nodes.append({"id": f"C{r.from_id}", "label": f"client {r.from_id}", "kind": "CUSTOMER"})
            edges.append({"source": f"C{customer_id}", "target": f"C{r.from_id}",
                          "type": r.relation_type, "confidence": r.confidence})
    for im in identities:
        nodes.append({"id": f"N{im.network_identity_id}", "kind": "NETWORK",
                      "network_customer_id": im.network_identity_id})
        edges.append({"source": f"C{customer_id}", "target": f"N{im.network_identity_id}",
                      "type": "MATCHES", "confidence": im.confidence})

    return {"success": True, "data": {
        "customer_id": customer_id,
        "multi_branch": len(identities) > 0,
        "degree": len(rels),
        "nodes": nodes, "edges": edges,
        "pseudonym": cust.network_customer_id,
    }, "meta": {"requestId": "customer-network"}}


@router.get("/identities")
async def list_identities(user: CurrentUser = Depends(require("read:screening")),
                          db: AsyncSession = Depends(get_db),
                          page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    q = select(NetworkIdentity)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(NetworkIdentity.created_at.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    data = []
    for ident in rows:
        matches = (await db.execute(
            select(IdentityMatch.customer_id).where(IdentityMatch.network_identity_id == ident.id))).scalars().all()
        data.append({"network_customer_id": ident.id, "customers": matches,
                     "created_at": ident.created_at.isoformat()})
    return {"success": True, "data": data,
            "meta": {"page": page, "limit": limit, "total": total, "requestId": "identities"}}


@router.post("/identities/match")
async def match_identity(request: Request,
                         user: CurrentUser = Depends(require("manage:screening")),
                         db: AsyncSession = Depends(get_db)):
    """Déclare la correspondance d'un client local avec une identité réseau."""
    body = await request.json()
    customer_id = int(body["customer_id"])
    network_id = str(body["network_customer_id"])
    cust = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if cust is None:
        raise AppError("CUSTOMER_NOT_FOUND", "Client introuvable", status=404)
    ident = (await db.execute(
        select(NetworkIdentity).where(NetworkIdentity.id == network_id))).scalar_one_or_none()
    if ident is None:
        ident = NetworkIdentity(id=network_id)
        db.add(ident)
        await db.flush()
    db.add(IdentityMatch(customer_id=customer_id, network_identity_id=network_id,
                         confidence=float(body.get("confidence", 1.0))))
    cust.network_customer_id = network_id
    await audit(db, actor_id=user.id, actor_role=user.role, action="IDENTITY_MATCHED",
                entity_type="CUSTOMER", entity_id=customer_id,
                new_value={"network_id": network_id},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"matched": True},
            "meta": {"requestId": request.state.request_id}}