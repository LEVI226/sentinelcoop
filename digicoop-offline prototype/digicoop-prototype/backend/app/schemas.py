from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel


class SyncItem(BaseModel):
    uuid: str
    entity_type: Literal["client", "transaction", "alert"]
    agency_id: str
    payload: Dict[str, Any]
    client_ts: Optional[str] = None


class PushRequest(BaseModel):
    agency_id: str
    items: List[SyncItem]


class PushResultItem(BaseModel):
    uuid: str
    status: Literal["synced", "error"]
    detail: Optional[str] = None


class PushResponse(BaseModel):
    results: List[PushResultItem]
    server_time: str


class WatchlistEntryOut(BaseModel):
    id: str
    full_name: str
    category: str
    source: str
    updated_at: str


class PullResponse(BaseModel):
    watchlist: List[WatchlistEntryOut]
    server_time: str


class AlertOut(BaseModel):
    id: str
    client_id: str
    matched_name: Optional[str] = None
    match_score: float
    severity: str
    decision: str
    created_at: str


class DecisionRequest(BaseModel):
    decision: Literal["false_positive", "confirmed", "reported"]
