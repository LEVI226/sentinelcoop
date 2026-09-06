"""
Alimente watchlist_entries avec des noms strictement synthétiques.

Conforme à la règle « aucune donnée réelle » du briefing hackathon : ce ne
sont pas des extraits de vraies listes de sanctions ni de vrais profils PPE,
juste de quoi démontrer le mécanisme de filtrage et de synchronisation
descendante en local pendant le hackathon.

Usage : python -m app.seed_watchlist
"""
import uuid
import datetime as dt

from .database import SessionLocal, Base, engine
from . import models

Base.metadata.create_all(bind=engine)

SAMPLE_WATCHLIST = [
    ("Amadou TRAORE-DIALLO", "SANCTION"),
    ("Fatoumata KEITA-SANOGO", "PPE"),
    ("Ibrahim OUEDRAOGO-COMPAORE", "SANCTION"),
    ("Aissata BARRY-CISSOKHO", "PPE"),
]


def run():
    db = SessionLocal()
    created = 0
    for name, category in SAMPLE_WATCHLIST:
        exists = db.query(models.WatchlistEntry).filter_by(full_name=name).first()
        if exists:
            continue
        db.add(models.WatchlistEntry(
            id=str(uuid.uuid4()), full_name=name, category=category,
            source="SYNTHETIC-DEMO", updated_at=dt.datetime.utcnow(),
        ))
        created += 1
    db.commit()
    db.close()
    print(f"{created} entrée(s) synthétique(s) ajoutée(s) à watchlist_entries.")


if __name__ == "__main__":
    run()
