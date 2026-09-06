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
