"""Moteur de screening — normalisation, matching exact/fuzzy/alias/phonétique
avec conservation de la version de liste (CDC §16-17).
"""
from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screening import (
    ScreeningEntity,
    ScreeningListVersion,
    ScreeningMatch,
    ScreeningRun,
)


def normalize(text: str) -> str:
    """Normalise (minuscule, sans accents, espaces réduits)."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def phonetic_key(text: str) -> str:
    """Clé phonétique simplifiée (Soundex-like) pour matcher les variantes de translittération."""
    n = normalize(text)
    # Voyelles/lettres variables neutralisées dans les groupes de consonnes
    n = re.sub(r"[aeiouyh]", "", n)
    # Consonnes équivalentes (variantes francophones/anglophones)
    replacements = {
        "ph": "f", "th": "t", "kh": "k", "ch": "sh",
        "c": "k", "q": "k", "z": "s", "j": "g",
    }
    for a, b in replacements.items():
        n = n.replace(a, b)
    return n[:12]


def similarity(a: str, b: str) -> float:
    """Similarité simple (ratio des plus longues sous-séquences approximées)."""
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.9
    # Similarité de séquences (Levenshtein simplifié via difflib)
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


class ScreeningEngine:
    """Exécute un screening contre les entités de la liste actuelle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_current_list_versions(self):
        res = await self.db.execute(
            select(ScreeningListVersion).where(ScreeningListVersion.is_current.is_(True))
        )
        return res.scalars().all()

    async def run_customer(self, *, subject_id: int, full_name: str,
                           birthday: str | None = None, country: str | None = None,
                           executed_by: int | None = None) -> ScreeningRun:
        versions = await self.get_current_list_versions()
        run = ScreeningRun(subject_type="CUSTOMER", subject_id=subject_id, executed_by=executed_by)
        self.db.add(run)
        await self.db.flush()

        matches = []
        for version in versions:
            res = await self.db.execute(
                select(ScreeningEntity).where(ScreeningEntity.list_version_id == version.id)
            )
            entities = res.scalars().all()
            for ent in entities:
                score = similarity(full_name, ent.full_name)
                match_type = self._classify(full_name, ent)
                if score >= 0.6:
                    m = ScreeningMatch(
                        run_id=run.id,
                        entity_id=ent.id,
                        list_version_id=version.id,
                        score=round(score, 3),
                        match_type=match_type,
                    )
                    self.db.add(m)
                    matches.append(m)
        await self.db.flush()
        return run

    def _classify(self, subject_name: str, entity: ScreeningEntity) -> str:
        if normalize(subject_name) == normalize(entity.full_name):
            return "EXACT"
        if phonetic_key(subject_name) == phonetic_key(entity.full_name):
            return "PHONETIC"
        return "FUZZY"
