"""Service d'audit append-only (CDC §29)."""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extra import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, *, actor_id: Optional[int], actor_role: str, action: str,
                  entity_type: str = "", entity_id: Optional[int] = None,
                  old_value: Optional[dict] = None, new_value: Optional[dict] = None,
                  reason: str = "", request_id: str = "", ip_address: str = "",
                  device_id: str = "", metadata: Optional[dict] = None) -> AuditLog:
        entry = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=json.dumps(old_value, default=str) if old_value is not None else "",
            new_value=json.dumps(new_value, default=str) if new_value is not None else "",
            reason=reason,
            request_id=request_id,
            ip_address=ip_address,
            device_id=device_id,
            metadata_json=json.dumps(metadata, default=str) if metadata else "{}",
        )
        self.db.add(entry)
        await self.db.flush()
        return entry


async def audit(db: AsyncSession, *, actor_id: Optional[int] = None,
                actor_role: str = "", action: str, entity_type: str = "",
                entity_id: Optional[int] = None, old_value: Optional[dict] = None,
                new_value: Optional[dict] = None, reason: str = "",
                request_id: str = "", ip_address: str = "") -> None:
    await AuditService(db).log(
        actor_id=actor_id, actor_role=actor_role, action=action,
        entity_type=entity_type, entity_id=entity_id,
        old_value=old_value, new_value=new_value, reason=reason,
        request_id=request_id, ip_address=ip_address,
    )
