"""Modèles : moteur de règles (versionné, CDC §15)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    rule_type: Mapped[str] = mapped_column(String(40), default="THRESHOLD")  # THRESHOLD|STRUCTURING|FREQUENCY|VELOCITY|PROFILE_DEVIATION|GEOGRAPHIC|PEP|SANCTIONS|NETWORK|ACCOUNT_AGE|SOURCE_OF_FUNDS|CUSTOM
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    current_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rule_versions.id"), nullable=True
    )

    versions: Mapped[list["RuleVersion"]] = relationship(
        back_populates="rule", foreign_keys="RuleVersion.rule_id"
    )


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    config_json: Mapped[str] = mapped_column(Text, default="{}")  # seuil, seuil_48h, etc.
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conditions: Mapped[list["RuleCondition"]] = relationship(back_populates="version")
    actions: Mapped[list["RuleAction"]] = relationship(back_populates="version")
    rule: Mapped[Rule] = relationship(
        back_populates="versions", foreign_keys=[rule_id]
    )


class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_version_id: Mapped[int] = mapped_column(ForeignKey("rule_versions.id", ondelete="CASCADE"), index=True)
    field: Mapped[str] = mapped_column(String(100))
    operator: Mapped[str] = mapped_column(String(20))   # gt | gte | lt | lte | eq | in
    value: Mapped[str] = mapped_column(String(100))

    version: Mapped[RuleVersion] = relationship(back_populates="conditions")


class RuleAction(Base):
    __tablename__ = "rule_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_version_id: Mapped[int] = mapped_column(ForeignKey("rule_versions.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(50))    # CREATE_ALERT
    severity: Mapped[str] = mapped_column(String(20), default="HIGH")
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM")

    version: Mapped[RuleVersion] = relationship(back_populates="actions")


class RuleExecution(Base):
    __tablename__ = "rule_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_version_id: Mapped[int] = mapped_column(ForeignKey("rule_versions.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))   # TRANSACTION | CUSTOMER
    target_id: Mapped[int] = mapped_column(Integer, index=True)
    matched: Mapped[bool] = mapped_column(Boolean, default=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
