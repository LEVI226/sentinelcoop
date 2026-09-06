"""Moteur de règles — détection basée sur des conditions configurables (CDC §15).

Implémente des évaluateurs pour les types de règles courants. Les règles sont
définies en base (collège) et évaluées sans modification du code métier.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class RuleEvaluator:
    """Évalue une règle sur un ensemble de transactions récentes d'un client."""

    def evaluate_threshold(self, config: dict, transactions: list) -> bool:
        """Seuil sur le montant d'une transaction."""
        threshold = _num(config.get("min_amount", 0))
        return any(_num(t.get("amount", 0)) >= threshold for t in transactions)

    def evaluate_structuring(self, config: dict, transactions: list, now=None) -> bool:
        """STRUCTURING_48H : >=N transactions en 48h, somme > seuil, montants proches du seuil.

        EXEMPLE CDC §15 :
          COUNT(transactions within 48h) >= 3
          AND SUM(amounts) > configuredThreshold
          AND all amounts are close to threshold
        """
        now = now or datetime.now()
        window = timedelta(hours=_num(config.get("window_hours", 48)))
        min_count = int(config.get("min_count", 3))
        threshold = _num(config.get("min_amount", 1000000))
        ratio = _num(config.get("close_ratio", 0.7))

        window_txs = []
        for t in transactions:
            d = t.get("transaction_date")
            try:
                dt = datetime.fromisoformat(str(d))
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                if now - dt <= window:
                    window_txs.append(t)
            except Exception:
                continue

        if len(window_txs) < min_count:
            return False
        total = sum(_num(t.get("amount", 0)) for t in window_txs)
        if total <= threshold:
            return False
        # Tous les montants proches du seuil
        if threshold > 0:
            for t in window_txs:
                amt = _num(t.get("amount", 0))
                if amt < threshold * ratio:
                    return False
        return True

    def evaluate_frequency(self, config: dict, transactions: list, now=None) -> bool:
        """Fréquence : nombre de transactions sur une fenêtre >= seuil."""
        window = timedelta(hours=_num(config.get("window_hours", 24)))
        max_count = int(config.get("max_count", 10))
        now = now or datetime.now()
        count = 0
        for t in transactions:
            d = t.get("transaction_date")
            try:
                dt = datetime.fromisoformat(str(d))
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                if now - dt <= window:
                    count += 1
            except Exception:
                continue
        return count >= max_count

    def evaluate_velocity(self, config: dict, transactions: list, now=None) -> bool:
        """Vitesse : somme des montants sur une fenêtre >= seuil."""
        window = timedelta(hours=_num(config.get("window_hours", 24)))
        min_sum = _num(config.get("min_sum", 0))
        now = now or datetime.now()
        total = 0.0
        for t in transactions:
            d = t.get("transaction_date")
            try:
                dt = datetime.fromisoformat(str(d))
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                if now - dt <= window:
                    total += _num(t.get("amount", 0))
            except Exception:
                continue
        return total >= min_sum

    def evaluate_config(self, rule_type: str, config: dict, transactions: list,
                        now: Optional[datetime] = None) -> bool:
        fn = {
            "THRESHOLD": self.evaluate_threshold,
            "STRUCTURING": self.evaluate_structuring,
            "FREQUENCY": self.evaluate_frequency,
            "VELOCITY": self.evaluate_velocity,
        }.get(rule_type)
        if fn is None:
            return False
        return fn(config, transactions, now) if rule_type != "THRESHOLD" else fn(config, transactions)


rule_evaluator = RuleEvaluator()


def parse_config(config_json: str) -> dict:
    try:
        return json.loads(config_json or "{}")
    except Exception:
        return {}


def run_rule(rule_type: str, config_json: str, transactions: list,
             now: Optional[datetime] = None) -> dict:
    """Exécute une règle et renvoie la décision (+ détail)."""
    config = parse_config(config_json)
    matched = rule_evaluator.evaluate_config(rule_type, config, transactions, now)
    return {
        "matched": matched,
        "rule_type": rule_type,
        "config": config,
        "transaction_count": len(transactions),
    }
