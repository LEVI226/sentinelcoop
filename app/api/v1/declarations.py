"""Module DECLARATIONS DE SOUPCON et RESULTATS DE FILTRAGE — diagramme LBC/FT.

POST   /api/v1/declarations                 (créer une déclaration de soupçon)
GET    /api/v1/declarations                 (lister)
GET    /api/v1/declarations/:id
PATCH  /api/v1/declarations/:id             (statut)
GET    /api/v1/filtering-results            (résultats de filtrage)
POST   /api/v1/filtering-results/:id/decision   (décision de filtrage)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require
from app.core.errors import AppError
from app.database import get_db
from app.models.customer import Customer
from app.models.declaration import DeclarationSoupcon, ResultatFiltrage
from app.services.audit_service import audit

router = APIRouter(tags=["declarations"])


class DeclarationCreate(BaseModel):
    client_id: int
    alert_id: int | None = None
    case_id: int | None = None
    transaction_id: int | None = None
    descriptif: str = Field(min_length=5)
    montant_suspect: float | None = None
    devise: str = "XOF"
    cellule_destinataire: str = "CENTIF"


class DeclarationUpdate(BaseModel):
    statut: str | None = None
    descriptif: str | None = None


class DecisionFiltrage(BaseModel):
    decision: str = Field(pattern="AUTORISEE|EN_ATTENTE|REFUSEE")
    commentaire: str = ""


@router.post("/declarations")
async def create_declaration(body: DeclarationCreate, request: Request,
                             user: CurrentUser = Depends(require("manage:cases")),
                             db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Customer).where(Customer.id == body.client_id))
    if res.scalar_one_or_none() is None:
        raise AppError("CUSTOMER_NOT_FOUND", "Client inexistant", status=404)
    dec = DeclarationSoupcon(
        code=f"DEC-{await _next_code(db)}",
        client_id=body.client_id,
        alert_id=body.alert_id,
        case_id=body.case_id,
        transaction_id=body.transaction_id,
        descriptif=body.descriptif,
        montant_suspect=body.montant_suspect,
        devise=body.devise,
        cellule_destinataire=body.cellule_destinataire,
        declare_par=user.id,
        statut="BROUILLON",
    )
    db.add(dec)
    await db.flush()
    await audit(db, actor_id=user.id, actor_role=user.role, action="DECLARATION_CREATED",
                entity_type="DECLARATION", entity_id=dec.id,
                new_value={"client_id": body.client_id, "montant": body.montant_suspect},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(dec)
    return {"success": True, "data": _serialize(dec), "meta": {"requestId": request.state.request_id}}


async def _next_code(db: AsyncSession) -> str:
    res = await db.execute(select(func.count()).select_from(DeclarationSoupcon))
    return f"{res.scalar() + 1:05d}"


@router.get("/declarations")
async def list_declarations(user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db),
                            page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                            statut: str | None = None):
    q = select(DeclarationSoupcon)
    if statut:
        q = q.where(DeclarationSoupcon.statut == statut)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(DeclarationSoupcon.created_at.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    return {"success": True, "data": [_serialize(d) for d in rows],
            "meta": {"page": page, "limit": limit, "total": total, "requestId": "list"}}


@router.get("/declarations/{declaration_id}")
async def get_declaration(declaration_id: int, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DeclarationSoupcon).where(DeclarationSoupcon.id == declaration_id))
    dec = res.scalar_one_or_none()
    if dec is None:
        raise AppError("DECLARATION_NOT_FOUND", "Déclaration introuvable", status=404)
    return {"success": True, "data": _serialize(dec), "meta": {"requestId": "get"}}


@router.patch("/declarations/{declaration_id}")
async def update_declaration(declaration_id: int, body: DeclarationUpdate, request: Request,
                             user: CurrentUser = Depends(require("manage:cases")),
                             db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DeclarationSoupcon).where(DeclarationSoupcon.id == declaration_id))
    dec = res.scalar_one_or_none()
    if dec is None:
        raise AppError("DECLARATION_NOT_FOUND", "Déclaration introuvable", status=404)
    if body.statut:
        dec.statut = body.statut
    if body.descriptif:
        dec.descriptif = body.descriptif
    await audit(db, actor_id=user.id, actor_role=user.role, action="DECLARATION_UPDATED",
                entity_type="DECLARATION", entity_id=dec.id,
                new_value={"statut": dec.statut},
                request_id=request.state.request_id)
    await db.commit()
    await db.refresh(dec)
    return {"success": True, "data": _serialize(dec), "meta": {"requestId": request.state.request_id}}


@router.get("/filtering-results")
async def list_filtering_results(user: CurrentUser = Depends(get_current_user),
                                 db: AsyncSession = Depends(get_db),
                                 page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                                 decision: str | None = None):
    q = select(ResultatFiltrage)
    if decision:
        q = q.where(ResultatFiltrage.decision_filtrage == decision)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    rows = (await db.execute(q.order_by(ResultatFiltrage.date_filtrage.desc())
                              .offset((page-1)*limit).limit(limit))).scalars().all()
    return {"success": True, "data": [{
        "id": r.id, "transaction_id": r.transaction_id, "liste_id": r.liste_id,
        "decision_filtrage": r.decision_filtrage, "score_correspondance": r.score_correspondance,
        "status": r.statut, "date_filtrage": r.date_filtrage.isoformat(),
        "commentaire": r.commentaire,
    } for r in rows], "meta": {"page": page, "limit": limit, "total": total, "requestId": "list"}}


@router.post("/filtering-results/{result_id}/decision")
async def decide_filtering(result_id: int, body: DecisionFiltrage, request: Request,
                           user: CurrentUser = Depends(require("manage:screening")),
                           db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ResultatFiltrage).where(ResultatFiltrage.id == result_id))
    r = res.scalar_one_or_none()
    if r is None:
        raise AppError("FILTERING_NOT_FOUND", "Résultat introuvable", status=404)
    r.decision_filtrage = body.decision
    r.commentaire = body.commentaire
    await audit(db, actor_id=user.id, actor_role=user.role, action="FILTERING_DECIDED",
                entity_type="FILTERING_RESULT", entity_id=r.id,
                new_value={"decision": body.decision},
                request_id=request.state.request_id)
    await db.commit()
    return {"success": True, "data": {"id": r.id, "decision_filtrage": r.decision_filtrage},
            "meta": {"requestId": request.state.request_id}}


def _serialize(d: DeclarationSoupcon) -> dict:
    return {
        "id": d.id, "code": d.code, "client_id": d.client_id,
        "alert_id": d.alert_id, "case_id": d.case_id, "transaction_id": d.transaction_id,
        "date_declaration": d.date_declaration.isoformat() if d.date_declaration else None,
        "descriptif": d.descriptif, "montant_suspect": d.montant_suspect,
        "devise": d.devise, "statut": d.statut,
        "cellule_destinataire": d.cellule_destinataire, "declare_par": d.declare_par,
    }