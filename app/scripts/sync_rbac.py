"""Synchronise permissions et rôles système depuis le registre RBAC.

Pensez-y à chaque évolution de `app/core/rbac.py` : ce script insère les
nouvelles permissions et reconstruit les liens rôle -> permissions pour les
rôles système (l'initiale se fait par `python -m app.scripts.seed`).

Usage : python -m app.scripts.sync_rbac
"""
from sqlalchemy import select

import app.models  # noqa: F401
from app.core.async_utils import run_async
from app.core.rbac import PERMISSIONS, SYSTEM_ROLES
from app.database import AsyncSessionLocal
from app.models.auth import Permission, Role, role_permissions


async def run() -> None:
    async with AsyncSessionLocal() as db:
        # 1. Permissions manquantes
        known = {p.code: p for p in (await db.execute(select(Permission))).scalars()}
        for code, name in PERMISSIONS.items():
            if code not in known:
                db.add(Permission(code=code, name=name, module=code.split(":")[-1]))
        await db.flush()

        perms = {p.code: p for p in (await db.execute(select(Permission))).scalars()}

        # 2. Rôles système manquants
        roles = {r.code: r for r in (await db.execute(select(Role))).scalars()}
        for code in SYSTEM_ROLES:
            if code not in roles:
                db.add(Role(code=code, name=code.replace("_", " ").title(), is_system=True))
        await db.flush()
        roles = {r.code: r for r in (await db.execute(select(Role))).scalars()}

        # 3. Reconstruire les liens rôle -> permission (rôles système uniquement)
        await db.execute(role_permissions.delete())
        for rcode, pcs in SYSTEM_ROLES.items():
            for pc in pcs:
                if pc in perms:
                    await db.execute(role_permissions.insert().values(
                        role_id=roles[rcode].id, permission_id=perms[pc].id)
                    )
        await db.commit()
        print("[sync_rbac] Permissions et rôles système réconciliés.")


if __name__ == "__main__":
    run_async(run())