"""Initialisation de la base : crée toutes les tables.

Usage : python -m app.scripts.init_db
"""
import app.models  # noqa: F401  (enregistre tous les modèles)
from app.core.async_utils import run_async
from app.database import Base, engine


async def run() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[init_db] Tables créées (create_all).")


if __name__ == "__main__":
    run_async(run())