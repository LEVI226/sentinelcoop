"""Schémas : alertes, cas, règles, screening, branches."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

ALERT_STATUSES = ["NEW", "TO_REVIEW", "IN_PROGRESS", "PENDING", "ESCALATED",
                  "CONFIRMED", "DISMISSED", "CLOSED"]


class AlertCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str = ""
    severity: str = Field(default="MEDIUM")
    priority: str = Field(default="MEDIUM")
    customer_id: Optional[int] = None
    transaction_id: Optional[int] = None
    branch_id: Optional[int] = None
    source: str = "MANUAL"


class AlertUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="|".join(ALERT_STATUSES))
    priority: Optional[str] = None
    severity: Optional[str] = None


class AlertAssign(BaseModel):
    user_id: int


class AlertCommentBody(BaseModel):
    body: str = Field(min_length=1)


class AlertInfoRequest(BaseModel):
    request_type: str = "IDENTITY_DOCUMENT"
    details: str = ""


# --- Case Management ---
class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str = ""
    customer_id: Optional[int] = None
    alert_ids: list[int] = []


class CaseNoteBody(BaseModel):
    body: str = Field(min_length=1)


class CaseTaskBody(BaseModel):
    title: str = Field(min_length=2)
    assigned_to: Optional[int] = None


class CaseDecisionBody(BaseModel):
    decision: str = Field(pattern="NFA|CONFIRMED|ESCALATE_TO_AUTHORITY|CLOSE|OTHER")
    reason: str = ""


# --- Rules ---
class RuleCreate(BaseModel):
    code: str = Field(min_length=3, max_length=80)
    name: str
    rule_type: str = Field(default="THRESHOLD")
    description: str = ""
    config_json: str = "{}"


# --- Screening ---
class ScreeningResult(BaseModel):
    run_id: int
    subject_type: str
    subject_id: int
    status: str
    matches: list = []


# --- Branches ---
class BranchCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    cooperative_id: Optional[int] = None
    city: str = ""
    country: str = ""
    manager_name: str = ""


class BranchRiskProfileUpdate(BaseModel):
    cash_exposure: int = Field(ge=0, le=100)
    geographical_exposure: int = Field(ge=0, le=100)
    economic_activity_exposure: int = Field(ge=0, le=100)