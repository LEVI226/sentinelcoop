"""
Connexion à la base centrale.

Cible réelle : PostgreSQL (voir docker-compose.yml à la racine).
Un DATABASE_URL non défini retombe sur un fichier SQLite local, uniquement
pour pouvoir lancer et tester l'API en quelques secondes pendant le hackathon,
sans dépendre d'un serveur Postgres déjà démarré.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./central_dev.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
