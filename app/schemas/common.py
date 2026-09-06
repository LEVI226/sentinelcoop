"""Schémas communs de validation."""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=200)
    total: int = 0


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = {}


class OKResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    meta: dict = {}



class ListResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T] = []
    meta: Page = Page()