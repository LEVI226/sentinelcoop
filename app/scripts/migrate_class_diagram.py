"""Migration légère : ajoute alert_type et crée les tables du diagramme.

Usage : python -m app.scripts.migrate_class_diagram
"""
from sqlalchemy import text

import app.models  # noqa: F401
from app.core.async_utils import run_async
from app.database import Base, engine


async def run():
    async with engine.begin() as conn:
        # Colonne alert_type (si absente)
        res = await conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='alerts' AND column_name='alert_type'"
        ))
        if res.scalar() is None:
            await conn.execute(text(
                "ALTER TABLE alerts ADD COLUMN alert_type VARCHAR(20) DEFAULT 'CONFORMITE' NOT NULL"
            ))
            print("[migrate] alerts.alert_type ajouté")
        else:
            print("[migrate] alerts.alert_type déjà présent")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[migrate] Tables diagramme créées (declaration_soupcons, resultats_filtrage)")


if __name__ == "__main__":
    run_async(run())