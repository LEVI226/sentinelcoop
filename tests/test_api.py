"""Tests d'intégration E2E — nécessitent le serveur lancé sur http://127.0.0.1:8000.

Lancer le serveur d'abord :
    .\\.venv\\Scripts\\python.exe run.py

Puis :
    .\\.venv\\Scripts\\python.exe -m pytest tests/test_api.py -q
"""
import json
import urllib.error
import urllib.request

import pytest

BASE = "http://127.0.0.1:8000/api/v1"


def _server_up():
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _server_up(), reason="Serveur CIF Guard non disponible sur 127.0.0.1:8000"
)


def call(method, path, token=None, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


@pytest.fixture(scope="module")
def admin():
    code, login = call("POST", "/auth/login",
                       body={"email": "admin@cifguard.net", "password": "CIFGuard@2026"})
    assert code == 200, f"login failed: {login}"
    return login


@pytest.fixture(scope="module")
def token(admin):
    return admin["data"]["access_token"]


def test_health():
    import urllib.request
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as r:
        j = json.loads(r.read().decode())
    assert r.status == 200 and j["success"]


def test_login_returns_jwt_refresh(admin):
    assert admin["data"]["access_token"]
    assert admin["data"]["refresh_token"].startswith("eyJ")


def test_me(token):
    code, j = call("GET", "/auth/me", token=token)
    assert code == 200
    assert j["data"]["email"] == "admin@cifguard.net"
    assert "superadmin" in j["data"]["roles"]


def test_refresh_rotation(admin):
    code, r = call("POST", "/auth/refresh", body={"refresh_token": admin["data"]["refresh_token"]})
    assert code == 200
    assert r["data"]["access_token"]
    assert r["data"]["refresh_token"].startswith("eyJ")


def test_dashboard_summary(token):
    code, j = call("GET", "/dashboard/summary", token=token)
    assert code == 200
    assert "clientsControlled" in j["data"]
    assert j["data"]["clientsControlled"] >= 1


def test_customers_searchable(token):
    code, j = call("GET", "/customers?query=diallo", token=token)
    assert code == 200
    assert any("Diallo" in (c["last_name"] or "") for c in j["data"])


def test_customer_detail_decrypts_pii(token):
    code, lst = call("GET", "/customers", token=token)
    cid = lst["data"][0]["id"]
    code, det = call("GET", f"/customers/{cid}", token=token)
    assert code == 200
    assert "first_name" in det["data"]


def test_customer_screen_produces_matches(token):
    code, lst = call("GET", "/customers", token=token)
    cid = lst["data"][0]["id"]
    code, j = call("POST", f"/customers/{cid}/screen", token=token, body={})
    assert code == 200
    assert "run_id" in j["data"]


def test_alerts_and_workflow(token):
    code, j = call("GET", "/alerts", token=token)
    assert code == 200 and len(j["data"]) >= 1
    aid = j["data"][0]["id"]
    code, up = call("PATCH", f"/alerts/{aid}", token=token, body={"status": "IN_PROGRESS"})
    assert code == 200


def test_cases_workflow(token):
    code, j = call("GET", "/cases", token=token)
    assert code == 200 and len(j["data"]) >= 1
    caid = j["data"][0]["id"]
    code, note = call("POST", f"/cases/{caid}/notes", token=token, body={"body": "note e2e"})
    assert code == 200


def test_rules_list(token):
    code, j = call("GET", "/rules", token=token)
    assert code == 200 and len(j["data"]) >= 1


def test_screening_versions(token):
    code, j = call("GET", "/screening/list-versions", token=token)
    assert code == 200 and len(j["data"]) >= 1


def test_audit_entries(token):
    code, j = call("GET", "/audit", token=token)
    assert code == 200 and len(j["data"]) >= 1


def test_branches_and_users(token):
    code, b = call("GET", "/branches", token=token)
    assert code == 200 and len(b["data"]) >= 1
    code, u = call("GET", "/users", token=token)
    assert code == 200 and len(u["data"]) >= 1


def test_reports_generation(token):
    code, j = call("POST", "/reports", token=token,
                   body={"report_type": "COMPLIANCE_SUMMARY", "format": "PDF"})
    assert code == 200
    assert j["data"]["status"] == "READY"


def test_unauthorized_access_rejected():
    code, j = call("GET", "/dashboard/summary")
    assert code == 401
    assert j["success"] is False


# ---------------------------------------------------------------------------
# Postes de travail (superadmin) — CDC §5
# ---------------------------------------------------------------------------
def test_superadmin_creates_and_deletes_poste(token):
    import uuid
    code_poste = f"PTE-{uuid.uuid4().hex[:6].upper()}"
    code, b = call("GET", "/branches", token=token)
    assert code == 200 and b["data"]
    branch_id = b["data"][0]["id"]
    code, c = call("POST", "/postes", token=token,
                   body={"code": code_poste, "name": "Guichet E2E", "branch_id": branch_id})
    assert code == 200, c
    poste_id = c["data"]["id"]
    code, lst = call("GET", "/postes", token=token)
    assert code == 200 and any(p["id"] == poste_id for p in lst["data"])
    # Suppression (soft) — le poste est désactivé, le code reste réservé
    code, d = call("DELETE", f"/postes/{poste_id}", token=token)
    assert code == 200 and d["data"]["is_active"] is False
    code, dup = call("POST", "/postes", token=token,
                     body={"code": code_poste, "name": "Guichet", "branch_id": branch_id})
    assert code in (409, 422)


def test_agent_cannot_manage_postes():
    code, login = call("POST", "/auth/login",
                       body={"email": "agent1@cifguard.net", "password": "CIFGuard@2026"})
    assert code == 200
    code, _ = call("POST", "/postes", token=login["data"]["access_token"],
                   body={"code": "PTE-X", "name": "X", "branch_id": 1})
    assert code == 403


def test_auditeur_cannot_manage_postes():
    code, login = call("POST", "/auth/login",
                       body={"email": "auditeur@cifguard.net", "password": "CIFGuard@2026"})
    assert code == 200
    code, _ = call("GET", "/postes", token=login["data"]["access_token"])
    assert code == 403


# ---------------------------------------------------------------------------
# Réinitialisation de mot de passe (superadmin/admin)
# ---------------------------------------------------------------------------
def test_superadmin_reset_password(token):
    import uuid
    uname = f"e2e_reset_{uuid.uuid4().hex[:6]}"
    email = f"{uname}@cifguard.net"
    code, c = call("POST", "/users", token=token,
                   body={"email": email, "username": uname,
                         "first_name": "E2E", "last_name": "Reset",
                         "role": "agent_caisse"})
    assert code == 200, c
    uid = c["data"]["id"]
    code, r = call("POST", f"/users/{uid}/reset-password", token=token,
                   body={"new_password": "NouveauMdp2026"})
    assert code == 200, r
    code, login = call("POST", "/auth/login",
                       body={"email": email, "password": "NouveauMdp2026"})
    assert code == 200, login


def test_reset_password_weak_rejected(token):
    code, u = call("GET", "/users", token=token)
    assert code == 200 and u["data"]
    uid = u["data"][0]["id"]
    code, _ = call("POST", f"/users/{uid}/reset-password", token=token,
                   body={"new_password": "short"})
    assert code == 422  # min_length=8 (validation pydantic)


# ---------------------------------------------------------------------------
# Journaux d'audit : non supprimables, conservation configurable
# ---------------------------------------------------------------------------
def test_audit_logs_are_not_deletable(token):
    code, lst = call("GET", "/audit", token=token)
    assert code == 200 and lst["data"]
    log_id = lst["data"][0]["id"]
    code, _ = call("DELETE", f"/audit/{log_id}", token=token)
    assert code in (404, 405)  # aucun endpoint de suppression n'existe


def test_settings_include_retention_days(token):
    code, j = call("GET", "/settings", token=token)
    assert code == 200
    assert "audit_log_retention_days" in j["data"]


def test_superadmin_configures_log_retention(token):
    code, j = call("PUT", "/settings", token=token,
                   body={"audit_log_retention_days": "730"})
    assert code == 200
    code, g = call("GET", "/settings", token=token)
    assert code == 200 and g["data"]["audit_log_retention_days"] == "730"
    # restauration de la valeur par défaut
    call("PUT", "/settings", token=token, body={"audit_log_retention_days": "365"})
