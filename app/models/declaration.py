"""Modèles : déclaration de soupçon, résultat de filtrage (class diagramme LBC/FT).

Liaison avec le diagramme :
- DeclarationSoupcon  → déclaration à l'autorité (FIU/CENTIF)
- ResultatFiltrage    → décision issue du filtrage d'une transaction
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeclarationSoupcon(Base):
    """Déclaration de soupçon (art. L.561 DDA). Liaisons : Client, AgentConformite, Alerte/Cas."""

    __tablename__ = "declaration_soupcons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transactions.id"), nullable=True
    )
    date_declaration: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    descriptif: Mapped[str] = mapped_column(Text, default="")
    montant_suspect: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    devise: Mapped[str] = mapped_column(String(3), default="XOF")
    statut: Mapped[str] = mapped_column(String(20), default="BROUILLON")  # BROUILLON|ENVOYEE|EN_ATTENTE|CLOTUREE
    cellule_destinataire: Mapped[str] = mapped_column(String(100), default="CENTIF")
    declare_par: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResultatFiltrage(Base):
    """Résultat d'un filtrage (class diagramme). Fait le lien entre ListeSanction,
    Transaction et Decision. Mapping vers ScreeningRun/ScreeningMatch existants."""

    __tablename__ = "resultats_filtrage"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    liste_id: Mapped[int] = mapped_column(ForeignKey("screening_lists.id"), index=True)
    decision_filtrage: Mapped[str] = mapped_column(String(20), default="AUTORISEE")  # AUTORISEE|EN_ATTENTE|REFUSEE
    score_correspondance: Mapped[float] = mapped_column(Float, default=0.0)
    statut: Mapped[str] = mapped_column(String(20), default="VALIDE")
    date_filtrage: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    commentaire: Mapped[str] = mapped_column(Text, default="")