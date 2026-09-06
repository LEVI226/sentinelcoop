"""Modèles : comptes et transactions."""
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
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref, foreign

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), index=True)
    account_type: Mapped[str] = mapped_column(String(20), default="SAVINGS")
    currency: Mapped[str] = mapped_column(String(3), default="XOF")
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE|FROZEN|CLOSED|DORMANT
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)

    customer: Mapped["Customer"] = relationship(back_populates="accounts")  # noqa: F821
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", lazy="selectin"
    )


class AccountHolder(Base):
    __tablename__ = "account_holders"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="OWNER")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id"), nullable=True, index=True
    )
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), index=True)
    counterparty_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("customers.id"), nullable=True, index=True
    )

    type: Mapped[str] = mapped_column(String(20))  # DEPOSIT|WITHDRAWAL|TRANSFER|PAYMENT|CASH_IN|CASH_OUT
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="XOF")
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    channel: Mapped[str] = mapped_column(String(30), default="BRANCH")
    purpose: Mapped[str] = mapped_column(String(200), default="")
    source_of_funds: Mapped[str] = mapped_column(String(200), default="")
    destination: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")
    monitoring_status: Mapped[str] = mapped_column(String(20), default="NOT_REVIEWED")  # NOT_REVIEWED|REVIEWED|FLAGGED
    risk_score: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[Optional[Account]] = relationship(back_populates="transactions")
    customer: Mapped["Customer"] = relationship(
        backref="transactions", foreign_keys=[customer_id]
    )  # noqa: F821
    counterparty: Mapped["Customer"] = relationship(
        foreign_keys=[counterparty_id]
    )  # noqa: F821
