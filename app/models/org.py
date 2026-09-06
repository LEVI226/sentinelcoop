"""Modèles : coopératives, caisses (branches), profils de risque locaux."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cooperative(Base):
    __tablename__ = "cooperatives"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(100), default="")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    branches: Mapped[list["Branch"]] = relationship(back_populates="cooperative")


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    cooperative_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cooperatives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    city: Mapped[str] = mapped_column(String(100), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    is_active: Mapped[bool] = mapped_column(default=True)
    # Contact du responsable local
    manager_name: Mapped[str] = mapped_column(String(200), default="")

    # Connectivité (CDC §35)
    last_successful_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    list_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    list_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    list_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_status: Mapped[str] = mapped_column(String(20), default="UP_TO_DATE")  # UP_TO_DATE|WARNING|OUTDATED|SYNC_FAILED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cooperative: Mapped[Optional[Cooperative]] = relationship(back_populates="branches")


class BranchRiskProfile(Base):
    """Profil de risque local de la caisse (CDC §28), versionné."""
    __tablename__ = "branch_risk_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    overall_risk: Mapped[int] = mapped_column(Integer, default=0)          # 0-100
    cash_exposure: Mapped[int] = mapped_column(Integer, default=0)
    geographical_exposure: Mapped[int] = mapped_column(Integer, default=0)
    economic_activity_exposure: Mapped[int] = mapped_column(Integer, default=0)
    monitoring_intensity: Mapped[int] = mapped_column(Integer, default=1)
    review_frequency_days: Mapped[int] = mapped_column(Integer, default=180)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OperatingZone(Base):
    __tablename__ = "operating_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    risk_level: Mapped[str] = mapped_column(String(20), default="MEDIUM")
