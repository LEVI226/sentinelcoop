"""Modèles : screening (filtrage). Vérsionnement des listes (CDC §16-17)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScreeningSource(Base):
    __tablename__ = "screening_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)  # SANCTIONS|PEP|INTERNAL_WATCHLIST|CUSTOM_WATCHLIST
    name: Mapped[str] = mapped_column(String(100))


class ScreeningList(Base):
    __tablename__ = "screening_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("screening_sources.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScreeningListVersion(Base):
    """Version d'une liste (CDC §17)."""
    __tablename__ = "screening_list_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("screening_lists.id"), index=True)
    version: Mapped[str] = mapped_column(String(30))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checksum: Mapped[str] = mapped_column(String(128), default="")
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(default=False)


class ScreeningEntity(Base):
    """Entité présente dans une liste (personne, organisation)."""
    __tablename__ = "screening_entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_version_id: Mapped[int] = mapped_column(ForeignKey("screening_list_versions.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(300), index=True)
    entity_type: Mapped[str] = mapped_column(String(30), default="INDIVIDUAL")
    country: Mapped[str] = mapped_column(String(100), default="")
    birth_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reason: Mapped[str] = mapped_column(String(300), default="")


class ScreeningAlias(Base):
    __tablename__ = "screening_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("screening_entities.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(300), index=True)


class ScreeningRun(Base):
    """Exécution d'un screening (par client ou transaction)."""
    __tablename__ = "screening_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_type: Mapped[str] = mapped_column(String(20))     # CUSTOMER | TRANSACTION
    subject_id: Mapped[int] = mapped_column(Integer, index=True)
    executed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")


class ScreeningMatch(Base):
    """Correspondance trouvée. Conserve la version de liste utilisée (CDC §17)."""
    __tablename__ = "screening_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("screening_runs.id", ondelete="CASCADE"), index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("screening_entities.id"), index=True)
    list_version_id: Mapped[int] = mapped_column(ForeignKey("screening_list_versions.id"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    match_type: Mapped[str] = mapped_column(String(20), default="FUZZY")  # EXACT|FUZZY|ALIAS|PHONETIC
    status: Mapped[str] = mapped_column(String(20), default="PENDING")    # PENDING|CONFIRMED|DISMISSED
    decision_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
