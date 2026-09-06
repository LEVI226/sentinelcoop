"""Tests unitaires — logique métier pure (sans base de données).

Exécution (depuis la racine du projet) :
    .\\.venv\\Scripts\\python.exe -m pytest tests -q
"""
import datetime

import pytest


# ---------------------------------------------------------------------------
# Security : chiffrement, blind index, mots de passe, JWT
# ---------------------------------------------------------------------------
class TestSecurity:
    def test_encrypt_field_roundtrip(self):
        from app.core import security
        ct = security.encrypt_field("Moussa Diallo", "customer.pii")
        assert ct.startswith("v1:")
        assert security.decrypt_field(ct, "customer.pii") == "Moussa Diallo"

    def test_encrypt_is_nondeterministic(self):
        from app.core import security
        a = security.encrypt_field("secret", "customer.pii")
        b = security.encrypt_field("secret", "customer.pii")
        assert a != b  # nonce aléatoire -> chiffrements différents

    def test_domain_separation(self):
        from app.core import security
        ct = security.encrypt_field("valeur", "customer.pii")
        with pytest.raises(Exception):
            security.decrypt_field(ct, "customer.phone")  # mauvaise sous-clé

    def test_blind_index_deterministic(self):
        from app.core import security
        assert security.blind_index("JeAN") == security.blind_index("jean")
        assert security.blind_index("abcd") != security.blind_index("abce")

    def test_password_hash_verify(self):
        from app.core import security
        h = security.hash_password("CIFGuard@2026")
        assert security.verify_password("CIFGuard@2026", h)
        assert not security.verify_password("mauvais", h)

    def test_jwt_access_roundtrip(self):
        from app.core import security
        t = security.create_access_token("u@x.com", 1, "superadmin", 1, 1, "sess1")
        payload = security.decode_token(t, expected_type="access")
        assert payload["uid"] == 1 and payload["sid"] == "sess1"

    def test_jwt_refresh_has_jti(self):
        from app.core import security
        t = security.create_refresh_token("u@x.com", 1, "sess1", jti="abc123")
        payload = security.decode_token(t, expected_type="refresh")
        assert payload["jti"] == "abc123"

    def test_jwt_wrong_type_rejected(self):
        from app.core import security
        t = security.create_access_token("u@x.com", 1, "admin", None, None, "s")
        with pytest.raises(Exception):
            security.decode_token(t, expected_type="refresh")


# ---------------------------------------------------------------------------
# RiskEngine : scores 0-100 et niveaux
# ---------------------------------------------------------------------------
class TestRiskEngine:
    def test_customer_score_bounds(self):
        from app.services.risk_engine import risk_engine
        r = risk_engine.customer_score(kyc_risk=100, pep_risk=100)
        assert 0 <= r["score"] <= 100
        assert r["level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def test_customer_score_low(self):
        from app.services.risk_engine import risk_engine
        r = risk_engine.customer_score(kyc_risk=0, pep_risk=0)
        assert r["score"] == 0
        assert r["level"] == "LOW"

    def test_explain_returns_string(self):
        from app.services.risk_engine import risk_engine
        r = risk_engine.customer_score(kyc_risk=80, pep_risk=0)
        assert isinstance(risk_engine.explain(r), str)

    def test_factor_explicability(self):
        from app.services.risk_engine import risk_engine
        r = risk_engine.customer_score(behavior_risk=90, kyc_risk=0)
        assert any(f["code"] == "BEHAVIOR" for f in r["factors"])
        # facteurs triés par contribution décroissante
        weights = [f["weight"] for f in r["factors"]]
        assert weights == sorted(weights, reverse=True)


# ---------------------------------------------------------------------------
# RuleEngine : détection de fractionnement (structuring), seuils, fréquence
# ---------------------------------------------------------------------------
class TestRuleEngine:
    def _txs(self, amounts, hours_ago, base=None):
        base = base or datetime.datetime(2026, 9, 1, 12, 0, 0)
        out = []
        for i, amt in enumerate(amounts):
            d = base - datetime.timedelta(hours=hours_ago[i])
            out.append({"amount": amt, "transaction_date": d.isoformat()})
        return out

    def test_structuring_detected(self):
        from app.services.rule_engine import rule_evaluator
        config = {"min_count": 3, "min_amount": 1000000, "window_hours": 48, "close_ratio": 0.7}
        now = datetime.datetime(2026, 9, 1, 12, 0, 0)
        txs = self._txs([900000, 950000, 880000], [2, 5, 10], now)  # 3 tx ~ seuil
        assert rule_evaluator.evaluate_structuring(config, txs, now) is True

    def test_structuring_not_detected_when_few(self):
        from app.services.rule_engine import rule_evaluator
        config = {"min_count": 3, "min_amount": 1000000, "window_hours": 48}
        now = datetime.datetime(2026, 9, 1, 12, 0, 0)
        txs = self._txs([900000, 950000], [2, 5], now)  # seulement 2
        assert rule_evaluator.evaluate_structuring(config, txs, now) is False

    def test_threshold_matched(self):
        from app.services.rule_engine import rule_evaluator
        assert rule_evaluator.evaluate_threshold({"min_amount": 5000000}, [{"amount": 6000000}])
        assert not rule_evaluator.evaluate_threshold({"min_amount": 5000000}, [{"amount": 1000}])

    def test_frequency_matched(self):
        from app.services.rule_engine import rule_evaluator
        config = {"max_count": 3, "window_hours": 24}
        now = datetime.datetime(2026, 9, 1, 12, 0, 0)
        txs = self._txs([100] * 5, [1, 2, 3, 4, 5], now)
        assert rule_evaluator.evaluate_frequency(config, txs, now) is True

    def test_unknown_rule_type_false(self):
        from app.services.rule_engine import run_rule
        r = run_rule("INCONNUE", "{}", [])
        assert r["matched"] is False


# ---------------------------------------------------------------------------
# ScreeningEngine : normalisation, phonétique, similarité (fonctions pures)
# ---------------------------------------------------------------------------
class TestScreeningUtils:
    def test_normalize(self):
        from app.services.screening_engine import normalize
        assert normalize("  Moussa   DIALLO ") == "moussa diallo"
        assert normalize("Élève") == "eleve"

    def test_similarity_exact(self):
        from app.services.screening_engine import similarity
        assert similarity("Moussa Diallo", "Moussa Diallo") == 1.0

    def test_similarity_substring(self):
        from app.services.screening_engine import similarity
        assert similarity("Diallo", "Moussa Diallo") == 0.9

    def test_similarity_near_high(self):
        from app.services.screening_engine import similarity
        assert similarity("Cheikh Ndiaye", "Cheick Ndiaye") > 0.6

    def test_phonetic_key_same_family(self):
        from app.services.screening_engine import phonetic_key
        # consonnes équivalentes : c/k, q/k, z/s
        assert phonetic_key("Cisse") == phonetic_key("Kisse")
        assert phonetic_key("Qamar") == phonetic_key("Kamar")
        assert phonetic_key("Zara") == phonetic_key("Sara")
        assert phonetic_key("Moussa Diallo") == phonetic_key("Moussa Diallo")

    def test_phonetic_key_empty(self):
        from app.services.screening_engine import phonetic_key
        assert phonetic_key("") == ""


# ---------------------------------------------------------------------------
# ABAC / RBAC (CurrentUser simulé)
# ---------------------------------------------------------------------------
class TestAbac:
    def _user(self, roles, branch=None):
        return type("U", (), {"roles": roles, "branch_id": branch, "cooperative_id": None})()

    def test_network_role_sees_all_branches(self):
        from app.core.abac import can_access_branch
        u = self._user(roles=["conformite_reseau"], branch=None)
        assert can_access_branch(u, 5) is True

    def test_branch_scoped(self):
        from app.core.abac import can_access_branch
        u = self._user(roles=["agent_caisse"], branch=2)
        assert can_access_branch(u, 2) is True
        assert can_access_branch(u, 3) is False

    def test_sensitive_confidential(self):
        from app.core.abac import can_read_sensitive
        assert can_read_sensitive(self._user(roles=["superadmin"]), "confidential") is True
        assert can_read_sensitive(self._user(roles=["agent_caisse"]), "confidential") is False

    def test_sensitive_public_always(self):
        from app.core.abac import can_read_sensitive
        assert can_read_sensitive(self._user(roles=["agent_caisse"]), "public") is True

    def test_abac_handles_string_roles(self):
        # CurrentUser.roles expose des str — _role_set doit gérer les deux formes
        from app.core.abac import can_access_branch, can_read_sensitive
        u = self._user(roles=["conformite_reseau"], branch=None)
        assert can_read_sensitive(u, "restricted") is True
        assert can_access_branch(u, 9) is True
