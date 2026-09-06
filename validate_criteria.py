"""Validation des 12 critères d'acceptation — CDC CIF Guard v1.0, section 58.

Chaque critère est évalué contre l'API réelle (serveur :8000).
Usage :
    python validate_criteria.py
Exit code 0 = les 12 critères sont OK.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

BASE = "http://127.0.0.1:8000/api/v1"
RESULTS = []


def _check(ok: bool, label: str, detail: str = ""):
    RESULTS.append(ok)
    print(f"[{'OK' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))


def _req(method, path, token=None, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def _login(email):
    code, j = _req("POST", "/auth/login",
                   body={"email": email, "password": "CIFGuard@2026"})
    if code != 200:
        return None, None, f"login {email} -> {code}"
    d = j["data"]
    _, me = _req("GET", "/auth/me", token=d["access_token"])
    return d["access_token"], me["data"], None


def _poll(fn, timeout=20, interval=1.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = fn()
        if r:
            return r
        time.sleep(interval)
    return None


def main():
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)
    except Exception:
        print("Serveur indisponible sur http://127.0.0.1:8000 — lancez :  python run.py")
        return 2

    # ---------------- Critère 1 : connexion selon le rôle ----------------
    roles_expect = {
        "admin@cifguard.net": "superadmin",
        "reseau@cifguard.net": "conformite_reseau",
        "auditeur@cifguard.net": "auditeur",
        "analyste@cifguard.net": "analyste_conformite",
        "caisse1@cifguard.net": "responsable_caisse",
        "agent1@cifguard.net": "agent_caisse",
    }
    sessions = {}
    ok_all = True
    for email, role in roles_expect.items():
        tok, me, err = _login(email)
        if tok is None:
            _check(False, "C1", f"{email}: {err}")
            ok_all = False
            continue
        sessions[email] = tok
        if role not in me["roles"]:
            ok_all = False
            _check(False, "C1", f"{email} role={me['roles']}")
    if ok_all:
        n_admin = len(_me_perms(sessions["admin@cifguard.net"]))
        n_agent = len(_me_perms(sessions["agent1@cifguard.net"]))
        _check(n_admin > n_agent, "C1 — Connexion selon le rôle",
               f"6 comptes conformes ; superadmin {n_admin} perms > agent {n_agent}")

    # ---------------- Critère 2 : périmètre de l'agent ----------------
    tok_admin = sessions["admin@cifguard.net"]
    _, cust_list = _req("GET", "/customers?limit=100", token=tok_admin)
    branches_of = {}
    for c in cust_list["data"]:
        branches_of.setdefault(c["branch_id"], c["id"])
    outside_cid = None
    agent_tok, agent_me, _ = _login("agent1@cifguard.net")
    ab = agent_me["branch_id"]
    inside_cid = branches_of.get(ab)
    for b, cid in branches_of.items():
        if b != ab:
            outside_cid = cid
            break
    ok = inside_cid is not None and outside_cid is not None
    if ok:
        code, _ = _req("GET", f"/customers/{outside_cid}", token=agent_tok)
        code_ok, _ = _req("GET", f"/customers/{inside_cid}", token=agent_tok)
        ok = code == 403 and code_ok == 200
    _check(ok, "C2 — Agent bloqué hors de son périmètre",
           f"caisse={ab} dans->200 hors->{code}")

    # ---------------- Critère 3 : transaction enregistrée + analysée ------
    first = cust_list["data"][0]
    ref = "VAL-" + uuid.uuid4().hex[:12].upper()
    body = {
        "reference": ref, "customer_id": first["id"], "branch_id": first["branch_id"],
        "type": "DEPOSIT", "amount": 750000, "currency": "XOF",
        "transaction_date": datetime.now(timezone.utc).isoformat(),
        "channel": "BRANCH", "purpose": "Depot revenus",
    }
    code, created = _req("POST", "/transactions", token=tok_admin, body=body)
    ok = code == 200 and created["data"]["analysis_pending"] is True
    rec = None
    if ok:
        rec = _poll(lambda: _req("GET", f"/transactions/{created['data']['id']}",
                                 token=tok_admin)[1]["data"].get("risk_score") is not None)
    ok = ok and rec is True
    _check(ok, "C3 — Transaction enregistrée et analysée",
           f"ref={ref}" if created.get("data") else f"code={code}")
    txn_id = created["data"]["id"] if created.get("data") else None

    # ---------------- Critère 4 : règle -> alerte automatique ---------------
    big = {
        **body, "reference": "VAL-" + uuid.uuid4().hex[:12].upper(),
        "amount": 6_000_000, "type": "TRANSFER",
    }
    code, bigc = _req("POST", "/transactions", token=tok_admin, body=big)
    rule_alert = None
    if code == 200:
        def _find():
            _, al = _req("GET", "/alerts?limit=100", token=tok_admin)
            return next((a for a in al["data"]
                         if a.get("transaction_id") == bigc["data"]["id"]
                         and a.get("source") == "RULE"
                         and a.get("rule_id")), None)
        rule_alert = _poll(_find)
    ok = rule_alert is not None and rule_alert["source"] == "RULE"
    _check(ok, "C4 — Règle déclenche une alerte automatique",
           f"HIGH_VALUE_TRANSFER -> AL-{rule_alert['id'] if rule_alert else '?'}")

    # ---------------- Critère 5 : affecter, escalader, clôturer ------------
    _, users = _req("GET", "/users", token=tok_admin)
    analyst = next((u["id"] for u in users["data"] if u.get("email", "").startswith("analyste")), None)
    if rule_alert and rule_alert.get("id"):
        aid = rule_alert["id"]
    else:
        _, al0 = _req("GET", "/alerts?limit=1", token=tok_admin)
        aid = al0["data"][0]["id"] if al0["data"] else None
    ok5 = 0
    if analyst and aid:
        code, j = _req("POST", f"/alerts/{aid}/assign", token=tok_admin,
                       body={"user_id": analyst})
        ok5 += code == 200 and j["data"]["status"] == "IN_PROGRESS"
        code, j = _req("POST", f"/alerts/{aid}/escalate", token=tok_admin)
        ok5 += code == 200 and j["data"]["status"] == "ESCALATED"
        code, j = _req("POST", f"/alerts/{aid}/close", token=tok_admin)
        ok5 += code == 200 and j["data"]["status"] == "CLOSED"
    _check(ok5 == 3, "C5 — Affectation -> escalade -> clôture",
           f"{ok5}/3 étapes sur alerte {aid}")

    # ---------------- Critère 6 : actions critiques dans l'audit -----------
    actions = ["LOGIN", "TRANSACTION_CREATED", "ALERT_ASSIGNED", "ALERT_ESCALATED",
               "ALERT_CLOSED"]
    found = {}
    for a in actions:
        code, j = _req("GET", f"/audit?action={a}&limit=5", token=tok_admin)
        found[a] = code == 200 and j["meta"]["total"] >= 1
    ok = all(found.values())
    _check(ok, "C6 — Actions critiques tracées dans l'audit",
           ", ".join(f"{k}={'OUI' if v else 'NON'}" for k, v in found.items()))

    # ---------------- Critère 7 : recherche multi-caisses / identité réseau -
    # Choisir un prénom réel partagé par des clients de caisses différentes
    from collections import defaultdict
    by_fn = defaultdict(set)
    for c in cust_list["data"]:
        if c.get("first_name"):
            by_fn[c["first_name"].lower()].add(c["branch_id"])
    search_term = max(by_fn, key=lambda k: len(by_fn[k]))
    code, found_ci = _req("GET",
                          f"/customers?search={urllib.parse.quote(search_term)}&limit=100",
                          token=tok_admin)
    branches_nb = len({c["branch_id"] for c in found_ci["data"]}) if code == 200 else 0
    ok = code == 200 and branches_nb >= 2
    detail = f"recherche '{search_term}' -> {len(found_ci['data'])} clients / {branches_nb} caisses"
    code, ids = _req("GET", "/network/identities", token=tok_admin)
    ok = ok and code == 200 and len(ids["data"]) >= 1
    c1 = cust_list["data"][0]["id"]
    if code == 200 and c1:
        code, nw = _req("GET", f"/network/customers/{c1}", token=tok_admin)
        ok = ok and code == 200 and nw["data"].get("pseudonym") is not None
        detail += f" ; graph C{c1} multi_branch={nw['data'].get('multi_branch')}"
    _check(ok, "C7 — Recherche multi-caisses via identité réseau", detail)

    # ---------------- Critère 8 : score de risque explicable ----------------
    code, risk = _req("GET", f"/customers/{c1}/risk", token=tok_admin)
    ok = (code == 200 and 0 <= risk["data"]["score"] <= 100
          and risk["data"]["level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
          and isinstance(risk["data"].get("explanation"), str))
    _check(ok, "C8 — Score de risque explicable",
           f"score={risk['data']['score']} level={risk['data']['level']}")

    # ---------------- Critère 9 : screening conserve la version -------------
    okay9 = True
    code, versions = _req("GET", "/screening/list-versions", token=tok_admin)
    okay9 = code == 200 and len(versions["data"]) >= 1
    # Import d'une liste -> nouvelle version hashée (SHA-256)
    code, imp = _req("POST", "/screening/lists/import", token=tok_admin, body={
        "list_name": "VAL GAFI " + uuid.uuid4().hex[:6].upper(),
        "source_code": "SANCTIONS", "version": "MANUAL",
        "items": [{"full_name": "Validation Criteres CIF Guard", "entity_type": "INDIVIDUAL"}],
    })
    okay9 = okay9 and code == 200 and len(imp["data"]["checksum"]) == 64
    # Un run conserve la version utilisée par match
    code, run = _req("POST", f"/customers/{c1}/screen", token=tok_admin, body={})
    okay9 = okay9 and code == 200 and run["data"].get("run_id")
    matches = _poll(lambda: (lambda res: res if res[1]["meta"]["total"] > 0 else None)(
        _req("GET", "/screening/matches?limit=50", token=tok_admin)))
    if matches:
        mlive = matches[1]["data"]
        codev, allv = _req("GET", "/screening/list-versions", token=tok_admin)
        known = {str(v["version"]) for v in allv["data"]}
        okay9 = okay9 and mlive and all(str(ma.get("list_version")) in known
                                        for ma in mlive if ma.get("list_version") is not None)
        okay9 = okay9 and any(ma.get("list_version") is not None for ma in mlive)
        detail9 = f"{len(mlive)} matches référencent une version connue"
    else:
        okay9 = False
        detail9 = "aucun match"
    _check(okay9, "C9 — Screening conserve la version de la liste", detail9)

    # ---------------- Critère 10 : fonctionnement en connectivité dégradée --
    evid = "DEGRADED-" + uuid.uuid4().hex[:8].upper()
    code, s1 = _req("POST", "/sync/events", token=tok_admin,
                    body={"device_id": evid, "sequence_number": 1,
                          "entity_type": "CUSTOMER", "payload": "{}"})
    code, s2 = _req("POST", "/sync/events", token=tok_admin,
                    body={"device_id": evid, "sequence_number": 1,
                          "entity_type": "CUSTOMER", "payload": "{}"})
    code, st = _req("GET", "/sync/status", token=tok_admin)
    ok = (code == 200 and s1["data"]["status"] == "SYNCED"
          and s2["data"]["status"] == "DUPLICATE"
          and any(e["status"] == "SYNCED" for e in st["data"]["events_by_status"]))
    _check(ok, "C10 — Connectivité dégradée : files sync idempotentes",
           f"SYNCED puis DUPLICATE pour {evid}")

    # ---------------- Critère 11 : dashboard depuis le backend --------------
    dash_routes = ["/dashboard/summary", "/dashboard/risk-distribution",
                   "/dashboard/alerts-trend", "/dashboard/priority-alerts",
                   "/dashboard/transaction-summary", "/dashboard/compliance-summary"]
    codes = {}
    for r in dash_routes:
        code, j = _req("GET", r, token=tok_admin)
        codes[r] = code
    html = open(r"app/static/admin/dashboard.html", encoding="utf-8").read()
    refs = [r for r in dash_routes if r.split("/")[-1] in html or r in html]
    ok = all(c == 200 for c in codes.values()) and len(refs) >= 4
    _check(ok, "C11 — Dashboard alimenté par le backend",
           f"{sum(1 for c in codes.values() if c==200)}/6 endpoints 200, {len(refs)} référencés dans le front")

    # ---------------- Critère 12 : rapports depuis données réelles ----------
    code, rep = _req("POST", "/reports", token=tok_admin,
                     body={"report_type": "COMPLIANCE_SUMMARY", "format": "PDF"})
    ok = code == 200 and rep["data"]["status"] == "READY"
    if ok:
        code, reps = _req("GET", "/reports", token=tok_admin)
        mine = next((r for r in reps["data"] if r["id"] == rep["data"]["id"]), None)
        ok = reps["data"] and mine is not None and mine["status"] == "READY" \
            and bool(mine.get("storage_key"))
    code, comp = _req("GET", "/dashboard/compliance-summary", token=tok_admin)
    ok = ok and code == 200 and len(comp["data"]["kyc"]) >= 1
    _check(ok, "C12 — Rapports générés depuis les données réelles",
           f"REPORT #{rep['data']['id']} READY + compliance réelle" if ok else f"code={code}")

    # ---------------- Synthèse -------------------------------------------------
    print("\n" + "=" * 70)
    n_ok = sum(1 for r in RESULTS if r)
    print(f"CIF Guard — Critères d'acceptation §58 : {n_ok}/12 OK")
    return 0 if n_ok == 12 else 1


def _me_perms(tok):
    _, me = _req("GET", "/auth/me", token=tok)
    return me["data"]["permissions"]


if __name__ == "__main__":
    sys.exit(main())