"""Modèles : clients, KYC, identité réseau, risque client.

Les champs PII sensibles sont stockés **chiffrés** (AES-256-GCM, HMAC blind-index)
conformément à l'exigence « chiffrement dernière génération des dossiers clients ».
"""
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    """Client. Les données sensibles sont chiffrées ; recherche via blind index."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), index=True)
    cooperative_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=True, index=True
    )

    # Identifiants local et réseau
    local_customer_id: Mapped[str] = mapped_column(String(50), index=True)
    network_customer_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    customer_type: Mapped[str] = mapped_column(String(30), default="INDIVIDUAL")  # INDIVIDUAL|COMPANY|ASSOCIATION|COOPERATIVE|OTHER_LEGAL_ENTITY

    # --- PII chiffrés (AES-256-GCM) ---
    first_name_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_name_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_of_birth_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    place_of_birth_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nationality_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gender_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occupation_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employer_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    declared_income_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Blind index (recherche sans déchiffrement) ---
    blind_last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    blind_first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    blind_email: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    blind_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # --- KYC / risque ---
    kyc_status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING|INCOMPLETE|UNDER_REVIEW|VERIFIED|REJECTED|EXPIRED
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    is_pep: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    accounts: Mapped[list["Account"]] = relationship(back_populates="customer")  # noqa: F821
    risk_scores: Mapped[list["CustomerRiskScore"]] = relationship(back_populates="customer")


class CustomerContact(Base):
    __tablename__ = "customer_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(30))          # phone|email|...
    value_enc: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(30), default="primary")
    country_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    street_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CustomerDocument(Base):
    __tablename__ = "customer_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    doc_type: Mapped[str] = mapped_column(String(50))      # IDENTITY_PASSPORT|PROOF_OF_ADDRESS|...
    doc_number_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="VALID")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BeneficialOwner(Base):
    """Bénéficiaire effectif (KYC entreprises)."""
    __tablename__ = "customer_beneficial_owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    full_name_enc: Mapped[str] = mapped_column(Text)
    ownership_pct: Mapped[float] = mapped_column(Float, default=0.0)
    nationality_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PePRelation(Base):
    __tablename__ = "customer_pep_relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    is_pep: Mapped[bool] = mapped_column(Boolean, default=False)
    pep_role_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CustomerRiskScore(Base):
    """Score de risque explicable (CDC §18 & §20)."""
    __tablename__ = "customer_risk_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    score: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(20))
    factors_json: Mapped[str] = mapped_column(Text, default="[]")   # [{code,weight},...]
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped[Customer] = relationship(back_populates="risk_scores")


class NetworkIdentity(Base):
    """Identité réseau pseudonymisée (CDC §11)."""
    __tablename__ = "network_identities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)   # network_customer_id pseudonymisé
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IdentityMatch(Base):
    """Lien entre un client local et une identité réseau."""
    __tablename__ = "identity_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    network_identity_id: Mapped[str] = mapped_column(ForeignKey("network_identities.id"), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
