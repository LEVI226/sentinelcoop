"""Schémas du module transactions."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

TRANSACTION_TYPES = ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "CASH_IN", "CASH_OUT"]


class TransactionCreate(BaseModel):
    reference: str = Field(min_length=3, max_length=50)
    customer_id: int
    account_id: Optional[int] = None
    branch_id: int
    counterparty_id: Optional[int] = None
    type: str = Field(pattern="|".join(TRANSACTION_TYPES))
    amount: float = Field(gt=0)
    currency: str = Field(default="XOF", min_length=3, max_length=3)
    transaction_date: datetime
    channel: str = "BRANCH"
    purpose: str = ""
    source_of_funds: str = ""
    destination: str = ""