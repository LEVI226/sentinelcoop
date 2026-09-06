"""Schémas du module clients / KYC."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

CUSTOMER_TYPES = ["INDIVIDUAL", "COMPANY", "ASSOCIATION", "COOPERATIVE", "OTHER_LEGAL_ENTITY"]
KYC_STATUSES = ["PENDING", "INCOMPLETE", "UNDER_REVIEW", "VERIFIED", "REJECTED", "EXPIRED"]


class CustomerCreate(BaseModel):
    branch_id: int
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: Optional[str] = None
    place_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    declared_income: Optional[float] = None
    customer_type: str = Field(default="INDIVIDUAL", pattern="|".join(CUSTOMER_TYPES))


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    declared_income: Optional[float] = None
    is_active: Optional[bool] = None


class CustomerReview(BaseModel):
    status: str = Field(pattern="|".join(KYC_STATUSES))
    comment: str = ""


class CustomerSearch(BaseModel):
    query: str = Field(min_length=1)