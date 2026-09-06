"""Modèles : demandes d'info, documents, relations réseau, rapports,
notifications, synchronisation, audit, paramètres système."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InformationRequest(Base):
    __tablename__ = "information_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    request_type: Mapped[str] = mapped_column(String(40))  # IDENTITY_DOCUMENT|SOURCE_OF_FUNDS|PROOF_OF_ADDRESS|TRANSACTION_JUSTIFICATION|BUSINESS_DOCUMENT|OTHER
    status: Mapped[str] = mapped_column(String(20), default="REQUESTED")  # REQUESTED|SENT|PARTIALLY_RECEIVED|RECEIVED|EXPIRED|CLOSED
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(30))  # CUSTOMER|ALERT|CASE|INFORMATION_REQUEST
    object_id: Mapped[int] = mapped_column(Integer, index=True)
    filename: Mapped[str] = mapped_column(String(300))
    content_type: Mapped[str] = mapped_column(String(100), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_key: Mapped[str] = mapped_column(String(400), default="")
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NetworkRelationship(Base):
    """Relations réseau (CDC §26) : OWNS, USES, TRANSFERRED_TO, ..."""
    __tablename__ = "network_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    relation_type: Mapped[str] = mapped_column(String(30))  # OWNS|USES|TRANSFERRED_TO|BELONGS_TO|BENEFICIAL_OWNER_OF|RELATED_TO|TRIGGERED
    from_type: Mapped[str] = mapped_column(String(20))
    from_id: Mapped[int] = mapped_column(Integer, index=True)
    to_type: Mapped[str] = mapped_column(String(20))
    to_id: Mapped[int] = mapped_column(Integer, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_type: Mapped[str] = mapped_column(String(40))  # COMPLIANCE_SUMMARY|KYC_REPORT|SCREENING_REPORT|TRANSACTION_MONITORING|ALERT_ACTIVITY|CASE_ACTIVITY|AUDIT_REPORT|RISK_REPORT
    format: Mapped[str] = mapped_column(String(10), default="PDF")  # PDF|XLSX|CSV
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING|READY|FAILED
    storage_key: Mapped[str] = mapped_column(String(400), default="")
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(20), default="IN_APP")
    event: Mapped[str] = mapped_column(String(50))  # NEW_ALERT|ALERT_ASSIGNED|...
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING|SYNCING|SYNCED|FAILED|CONFLICT
    direction: Mapped[str] = mapped_column(String(10), default="PUSH")  # PUSH|PULL
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, default="")


class SyncEvent(Base):
    """Événement hors-ligne (CDC §33-34). eventId = deviceId + sequence."""
    __tablename__ = "sync_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    sequence_number: Mapped[int] = mapped_column(Integer)
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING|SYNCING|SYNCED|FAILED|CONFLICT|DUPLICATE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    server_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Piste d'audit append-only (CDC §29)."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    actor_role: Mapped[str] = mapped_column(String(50), default="")
    action: Mapped[str] = mapped_column(String(60), index=True)  # LOGIN|CUSTOMER_CREATED|...
    entity_type: Mapped[str] = mapped_column(String(40), default="")
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    old_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    request_id: Mapped[str] = mapped_column(String(60), default="")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    device_id: Mapped[str] = mapped_column(String(200), default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
