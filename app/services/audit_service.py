"""Service d'audit append-only (CDC §29).

Le journal est destine a etre inalterable : aucun endpoint ne permet de
supprimer une entree a la demande (meme le superadmin). Seule la purge
automatique periodique, basee sur la duree de conservation configuree dans
`system_settings` (cle `audit_log_retention_days`, defaut
`AUDIT_LOG_RETENTION_DAYS`), retire les entrees obsoletes.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.extra import AuditLog, SystemSetting

RETENTION_SETTING_KEY = "audit_log_retention_days"


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


async def get_audit_retention_days(db: AsyncSession) -> int:
    """Duree de conservation (jours) configuree via system_settings, sinon defaut."""
    default = get_settings().AUDIT_LOG_RETENTION_DAYS
    row = (await db.execute(
        select(SystemSetting).where(SystemSetting.key == RETENTION_SETTING_KEY)
    )).scalar_one_or_none()
    if row is None:
        return default
    try:
        return max(1, int(str(row.value).strip()))
    except ValueError:
        return default


async def purge_obsolete_audit_logs(db: AsyncSession) -> int:
    """Supprime les entrees d'audit plus anciennes que la duree de conservation.

    Appelee uniquement par la tache de fond periodique (jamais via un
    endpoint) afin de preserver l'integrite du journal.
    """
    retention_days = await get_audit_retention_days(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    res = await db.execute(
        delete(AuditLog).where(AuditLog.timestamp < cutoff)
    )
    await db.commit()
    return res.rowcount or 0
