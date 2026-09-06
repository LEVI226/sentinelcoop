"""
Modèles de la base centrale (PostgreSQL en cible réelle).

Toutes les clés primaires métier (client, transaction, alerte) sont des
UUID générés côté terminal, jamais côté serveur : c'est ce qui permet
l'upsert idempotent lors du push (voir crud.py) et garantit qu'un lot
rejoué après une coupure réseau ne crée jamais de doublon.
"""
import datetime as dt
from sqlalchemy import Column, String, Float, DateTime, Text
from .database import Base


def now():
    return dt.datetime.utcnow()


class Client(Base):
    __tablename__ = "clients"
    id = Column(String, primary_key=True)
    agency_id = Column(String, index=True)
    full_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=True)
    id_document = Column(String, nullable=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True)
    client_id = Column(String, index=True, nullable=False)
    agency_id = Column(String, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="XOF")
    tx_type = Column(String, default="deposit")
    occurred_at = Column(DateTime, default=now)
    created_at = Column(DateTime, default=now)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True)
    agency_id = Column(String, index=True)
    client_id = Column(String, index=True)
    transaction_id = Column(String, nullable=True)
    matched_name = Column(String, nullable=True)
    match_score = Column(Float, default=0.0)
    severity = Column(String, default="informative")  # informative | blocking
    decision = Column(String, default="pending")  # pending | false_positive | confirmed | reported
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"
    id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False, index=True)
    category = Column(String, default="SANCTION")  # SANCTION | PPE
    source = Column(String, default="SYNTHETIC")
    updated_at = Column(DateTime, default=now, onupdate=now)


class SyncLog(Base):
    __tablename__ = "sync_log"
    id = Column(String, primary_key=True)
    agency_id = Column(String, index=True)
    entity_type = Column(String)
    entity_id = Column(String)
    direction = Column(String)  # push | pull
    status = Column(String)  # ok | error
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
