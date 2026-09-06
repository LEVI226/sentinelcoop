"""Seed database — données de démonstration CIF Guard (CDC §49-50).

Usage : python -m app.scripts.seed
"""
import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta

import app.models as models  # noqa: F401
from app.core import security
from app.core.async_utils import run_async
from app.core.rbac import PERMISSIONS as SECURITY_PERMISSIONS, SYSTEM_ROLES
from app.database import AsyncSessionLocal
from app.models.auth import Permission, Role, User, user_roles, role_permissions
from app.models.customer import (
    Customer, CustomerRiskScore, NetworkIdentity, IdentityMatch,
)
from app.models.org import Branch, BranchRiskProfile, Cooperative
from app.models.finance import Account, AccountHolder, Transaction
from app.models.rule import Rule, RuleVersion, RuleAction
from app.models.screening import (
    ScreeningSource, ScreeningList, ScreeningListVersion,
    ScreeningEntity, ScreeningAlias,
)
from app.models.alert import (
    Alert, Case, CaseNote, CaseDecision, AlertEvent,
    CaseAlert,
)
from app.models.extra import AuditLog, SystemSetting, NetworkRelationship
from app.services import customer_crypto
from app.services.risk_engine import RiskEngine

random.seed(42)


async def run():
    print("[seed] Démarrage...")

    async with AsyncSessionLocal() as db:
        # Garde idempotente : si l'utilisateur admin existe déjà, on s'arrête.
        from sqlalchemy import select
        from app.models.auth import User as SeedUser
        existing_admin = (await db.execute(select(SeedUser).where(SeedUser.username == "admin"))).scalar_one_or_none()
        if existing_admin is not None:
            print("[seed] Base déjà initialisée (admin présent) — sortie.")
            return
        # ------------------------------------------------------------------
        # 1. Permissions + rôles
        # ------------------------------------------------------------------
        perm_rows = {}
        for code, name in SECURITY_PERMISSIONS.items():
            p = Permission(code=code, name=name, module=code.split(":")[-1])
            db.add(p)
            perm_rows[code] = p
        await db.flush()

        role_objs = {}
        for code, perms in SYSTEM_ROLES.items():
            r = Role(code=code, name=code.replace("_", " ").title(), is_system=True)
            db.add(r)
            await db.flush()
            role_objs[code] = r

        await db.flush()
        # Attacher les permissions aux rôles
        import sqlalchemy as sa
        await db.execute(role_permissions.delete())
        for code, perm_codes in SYSTEM_ROLES.items():
            for pc in perm_codes:
                if pc in perm_rows:
                    await db.execute(role_permissions.insert().values(
                        role_id=role_objs[code].id, permission_id=perm_rows[pc].id))
        await db.commit()

        print("[seed] Rôles et permissions OK")

        # ------------------------------------------------------------------
        # 2. Coopérative + branches
        # ------------------------------------------------------------------
        coop = Cooperative(name="CIF Network S.A.", code="CIF", country="Sénégal")
        db.add(coop)
        await db.flush()

        branch_data = [
            ("DKR-01", "Dakar Plateau", "Dakar"),
            ("DKR-02", "Dakar Medina", "Dakar"),
            ("TLS-01", "Toulouse", "Toulouse"),
            ("YOF-01", "Yoff", "Dakar"),
            ("ZIG-01", "Ziguinchor", "Ziguinchor"),
        ]
        branches = []
        for code, name, city in branch_data:
            b = Branch(code=code, name=name, cooperative_id=coop.id, city=city,
                       country="Sénégal", manager_name=f"Gérant {city}",
                       sync_status="UP_TO_DATE")
            db.add(b)
            await db.flush()
            branches.append(b)
            db.add(BranchRiskProfile(
                branch_id=b.id, version=1,
                overall_risk=random.randint(10, 60),
                cash_exposure=random.randint(10, 80),
                geographical_exposure=random.randint(10, 70),
                economic_activity_exposure=random.randint(10, 60),
            ))
        await db.flush()

        print(f"[seed] {len(branches)} caisses OK")

        # ------------------------------------------------------------------
        # 3. Utilisateurs (un par rôle, sur une caisse)
        # ------------------------------------------------------------------
        users = {}
        user_defs = [
            ("admin", "admin@cifguard.net", "Admin", "Système", None, "superadmin"),
            ("audit", "auditeur@cifguard.net", "Awa", "Diop", None, "auditeur"),
            ("responsable", "reseau@cifguard.net", "Fatou", "Ndiaye", None, "conformite_reseau"),
            ("analyste", "analyste@cifguard.net", "Omar", "Sall", branches[0].id, "analyste_conformite"),
            ("resp_caisse1", "caisse1@cifguard.net", "Ibra", "Cissé", branches[0].id, "responsable_caisse"),
            ("agent1", "agent1@cifguard.net", "Mariama", "Ba", branches[0].id, "agent_caisse"),
            ("agent2", "agent2@cifguard.net", "Ndèye", "Faye", branches[1].id, "agent_caisse"),
        ]
        for uname, email, first, last, branch, role in user_defs:
            u = User(
                email=email, username=uname,
                password_hash=security.hash_password("CIFGuard@2026"),
                first_name=first, last_name=last,
                branch_id=branch,
                cooperative_id=coop.id,
                is_active=True,
            )
            db.add(u)
            await db.flush()
            users[uname] = u
            await db.execute(user_roles.insert().values(user_id=u.id, role_id=role_objs[role].id))
        await db.flush()
        print("[seed] Utilisateurs OK")

        # ------------------------------------------------------------------
        # 4. Listes de screening + entités fictives
        # ------------------------------------------------------------------
        sources = {}
        for code, name in [("SANCTIONS", "Liste sanctions"), ("PEP", "PEP"),
                           ("INTERNAL_WATCHLIST", "Watchlist interne")]:
            s = ScreeningSource(code=code, name=name)
            db.add(s)
            await db.flush()
            sources[code] = s

        for code, src in sources.items():
            sl = ScreeningList(source_id=src.id, name=f"{src.name} — démo", is_active=True)
            db.add(sl)
            await db.flush()
            version = ScreeningListVersion(
                list_id=sl.id, version="2026.01", published_at=datetime.now(),
                downloaded_at=datetime.now(), checksum=uuid.uuid4().hex,
                effective_from=datetime.now() - timedelta(days=30), is_current=True,
            )
            db.add(version)
            await db.flush()
            # Entités fictives
            demo_entities = {
                "SANCTIONS": [("Ousmane Traoré", "INDIVIDUAL", "ML"),
                              ("Alpha Barry", "INDIVIDUAL", "GN"),
                              ("Koffi Soudani", "INDIVIDUAL", "CI")],
                "PEP": [("Macky Sall", "INDIVIDUAL", "SN"),
                        ("Kaba Diallo", "INDIVIDUAL", "SN"),
                        ("Ibrahima Ndao", "INDIVIDUAL", "SN")],
                "INTERNAL_WATCHLIST": [("Moussa Diallo", "INDIVIDUAL", "SN"),
                                       ("Diallo Moussa", "INDIVIDUAL", "SN")],
            }
            for name, etype, country in demo_entities[code]:
                ent = ScreeningEntity(
                    list_version_id=version.id, full_name=name,
                    entity_type=etype, country=country,
                    reason="Démonstration",
                )
                db.add(ent)
                await db.flush()
                if code == "INTERNAL_WATCHLIST":
                    db.add(ScreeningAlias(entity_id=ent.id, alias=name))
        await db.flush()
        print("[seed] Listes screening OK")

        # ------------------------------------------------------------------
        # 5. Clients (20) + comptes + transactions
        # ------------------------------------------------------------------
        first_names = ["Moussa", "Amadou", "Fatou", "Awa", "Ousmane", "Mariama", "Ibrahima",
                        "Astou", "Cheikh", "Khadija", "Pape", "Aïcha", "Modou", "Bineta",
                        "Souleymane", "Rokhaya", "Lamine", "Ndeye", "Boubacar", "Diarra"]
        last_names = ["Diallo", "Diop", "Ndiaye", "Ba", "Sall", "Faye", "Gueye", "Sy",
                      "Cissé", "Sow", "Kane", "Mbow", "Diouf", "Seck", "Fall"]

        # Client A (scénario spectaculaire) : Moussa Diallo — 3 caisses, 7 comptes
        # identité réseau unique, fractionnement, alerte réseau, score CRITICAL
        net_id = "nid_" + uuid.uuid4().hex[:16]
        db.add(NetworkIdentity(id=net_id))
        await db.flush()

        customers = []
        popular_last = "Diallo"
        # 20 clients
        for i in range(1, 21):
            if i == 1:
                fn, ln = "Moussa", "Diallo"
            else:
                fn = random.choice(first_names)
                ln = random.choice(last_names)
                if ln == popular_last and i != 1:
                    ln = random.choice(last_names)
            branch = random.choice(branches)
            # Client A est dans 3 caisses différentes (DKR-01, DKR-02, TLS-01)
            if i == 1:
                branch = branches[0]
            cust = Customer(
                branch_id=branch.id,
                cooperative_id=coop.id,
                local_customer_id=f"LOC-{branch.code}-{i:04d}",
                network_customer_id=net_id if i == 1 else None,
                customer_type="INDIVIDUAL",
                kyc_status="VERIFIED" if i == 1 else random.choice(
                    ["PENDING", "VERIFIED", "UNDER_REVIEW", "VERIFIED"]),
                is_active=True,
            )
            data = {
                "first_name": fn, "last_name": ln,
                "date_of_birth": f"19{random.randint(60, 98)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "place_of_birth": random.choice(["Dakar", "Saint-Louis", "Thiès", "Kaolack", "Ziguinchor"]),
                "nationality": "Senegal",
                "gender": random.choice(["M", "F"]),
                "phone": f"+221 77 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
                "email": f"{fn.lower()}.{ln.lower()}{i}@mail.com".replace("é", "e").replace("è", "e"),
                "address": f"{random.randint(1,500)} Rue {random.choice(['Liberte','Scat Urbam','Bourguiba'])}",
                "occupation": random.choice(["Commerçant", "Enseignant", "Artisan", "Fonctionnaire", "Commerçant"]),
                "employer": f"Employeur {ln}",
                "declared_income": random.choice([150000, 250000, 350000, 500000, 750000]),
            }
            customer_crypto.apply_encryption(cust, data)
            db.add(cust)
            await db.flush()
            customers.append(cust)
            if i == 1:
                db.add(IdentityMatch(customer_id=cust.id, network_identity_id=net_id, confidence=1.0))

            # Comptes : Client A → 7 comptes répartis sur 3 caisses ;
            # autres → 1-3 comptes
            n_accounts = 7 if i == 1 else random.randint(1, 3)
            assigned_branches = [branches[0], branches[1], branches[2]] if i == 1 else [branch]
            for k in range(n_accounts):
                abranch = assigned_branches[k % len(assigned_branches)]
                acc = Account(
                    account_number=f"{abranch.code}-ACC-{i:04d}-{k+1:02d}",
                    customer_id=cust.id,
                    branch_id=abranch.id,
                    account_type=random.choice(["SAVINGS", "CHECKING", "SAVINGS"]),
                    currency="XOF",
                    status="ACTIVE",
                )
                db.add(acc)
                await db.flush()
                db.add(AccountHolder(account_id=acc.id, customer_id=cust.id, role="OWNER"))
        await db.flush()
        print("[seed] 20 clients OK (dont Client A: Moussa Diallo multi-caisses)")

        # ------------------------------------------------------------------
        # 6. Transactions (200) — avec le scénario de fractionnement pour Client A
        # ------------------------------------------------------------------
        txns = []
        now = datetime.now()
        for i in range(200):
            cust = customers[i % 20]
            accts = (await db.execute(
                Account.__table__.select().where(Account.__table__.c.customer_id == cust.id)
            )).fetchall()
            if not accts:
                continue
            acc = accts[0]
            # Type selon scénario Client A : fractionnement (CASH_IN / CASH_OUT petits montants)
            if cust.network_customer_id and (i % 3 == 0):
                ttype = random.choice(["CASH_IN", "CASH_OUT", "DEPOSIT"])
                amount = random.choice([950000, 980000, 1020000, 960000, 990000])  # proche du seuil
            else:
                ttype = random.choice(["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT"])
                amount = round(random.uniform(5000, 5000000), 0)
            ref = f"TXN-{now.strftime('%Y%m%d')}-{i+10000:06d}"
            txn = Transaction(
                reference=ref,
                customer_id=cust.id,
                account_id=acc.id,
                branch_id=acc.branch_id,
                counterparty_id=random.choice([c.id for c in customers[:5]]) if random.random() < 0.3 else None,
                type=ttype,
                amount=amount,
                currency="XOF",
                transaction_date=now - timedelta(hours=random.randint(1, 96)),
                channel=random.choice(["BRANCH", "MOBILE", "BRANCH"]),
                purpose="Commerce",
                source_of_funds="Revenus",
                destination="Paiement fournisseur" if ttype in ("PAYMENT",) else "",
                status="COMPLETED",
                monitoring_status="NOT_REVIEWED",
            )
            db.add(txn)
            await db.flush()
            txns.append(txn)
        await db.flush()
        print(f"[seed] {len(txns)} transactions OK")

        # ------------------------------------------------------------------
        # 7. Règles (STRUCTURING + THRESHOLD) + version
        # ------------------------------------------------------------------
        rule_s = Rule(
            code="STRUCTURING_48H", name="Fractionnement 48h",
            rule_type="STRUCTURING", description="≥3 opérations en 48h proches du seuil",
            is_active=True,
        )
        db.add(rule_s)
        await db.flush()
        rv_s = RuleVersion(rule_id=rule_s.id, version=1, is_current=True,
                           config_json=json.dumps({
                               "window_hours": 48, "min_count": 3,
                               "min_amount": 1000000, "close_ratio": 0.7,
                           }))
        db.add(rv_s)
        await db.flush()
        rule_s.current_version_id = rv_s.id
        db.add(RuleAction(rule_version_id=rv_s.id, action="CREATE_ALERT", severity="HIGH", priority="HIGH"))

        rule_t = Rule(
            code="HIGH_VALUE_TRANSFER", name="Transfert de forte valeur",
            rule_type="THRESHOLD", description="Montant ≥ 5 000 000",
            is_active=True,
        )
        db.add(rule_t)
        await db.flush()
        rv_t = RuleVersion(rule_id=rule_t.id, version=1, is_current=True,
                           config_json=json.dumps({"min_amount": 5000000}))
        db.add(rv_t)
        await db.flush()
        rule_t.current_version_id = rv_t.id
        db.add(RuleAction(rule_version_id=rv_t.id, action="CREATE_ALERT", severity="MEDIUM", priority="MEDIUM"))
        await db.flush()
        print("[seed] Règles OK")

        # ------------------------------------------------------------------
        # 8. Scores de risque (Client A : CRITICAL + explicable)
        # ------------------------------------------------------------------
        re = RiskEngine()
        client_a = customers[0]
        # Calcule le score avec contribution élevée (STRUCTURING + NETWORK + BRANCH)
        res = re.customer_score(
            kyc_risk=60, pep_risk=10, profile_risk=80,
            behavior_risk=85, network_risk=90, local_risk=70,
        )
        client_a.risk_score = res["score"]
        client_a.risk_level = res["level"]
        db.add(CustomerRiskScore(
            customer_id=client_a.id, score=res["score"], level=res["level"],
            factors_json=json.dumps(res["factors"]),
        ))
        # Scores pour les 19 autres
        for cust in customers[1:]:
            r = re.customer_score(
                kyc_risk=random.randint(0, 40),
                pep_risk=random.randint(0, 20),
                profile_risk=random.randint(0, 40),
                behavior_risk=random.randint(0, 50),
                network_risk=random.randint(0, 30),
                local_risk=random.randint(0, 40),
            )
            cust.risk_score = r["score"]
            cust.risk_level = r["level"]
            db.add(CustomerRiskScore(
                customer_id=cust.id, score=r["score"], level=r["level"],
                factors_json=json.dumps(r["factors"]),
            ))
        await db.flush()
        print(f"[seed] Scores OK — Client A : {res['score']} ({res['level']})")

        # ------------------------------------------------------------------
        # 9. Alertes (15) + cas (5) + demandes d'info
        # ------------------------------------------------------------------
        alert_defs = [
            ("AL-2026-001", "Fractionnement suspect 48h (Client A)", "STRUCTURING", "HIGH", "HIGH",
             client_a, branches[0].id, "RULE"),
            ("AL-2026-002", "Forte valeur — dépôt > seuil", "THRESHOLD", "MEDIUM", "MEDIUM",
             customers[3], branches[0].id, "RULE"),
            ("AL-2026-003", "Activité réseau multi-caisses", "NETWORK", "CRITICAL", "HIGH",
             client_a, None, "NETWORK"),
            ("AL-2026-004", "Matching screening interne", "SCREENING", "HIGH", "HIGH",
             customers[5], branches[1].id, "SCREENING"),
            ("AL-2026-005", "Vitesse de transactions élevée", "VELOCITY", "MEDIUM", "MEDIUM",
             customers[7], branches[2].id, "RULE"),
            ("AL-2026-006", "Retrait fractionné 24h", "STRUCTURING", "HIGH", "MEDIUM",
             customers[9], branches[0].id, "RULE"),
            ("AL-2026-007", "Virement vers zone à risque", "GEOGRAPHIC", "MEDIUM", "MEDIUM",
             customers[11], branches[1].id, "RULE"),
            ("AL-2026-008", "Variation forte par rapport au profil", "PROFILE_DEVIATION", "HIGH", "HIGH",
             customers[13], branches[3].id, "RULE"),
            ("AL-2026-009", "Somme encaissements 24h élevée", "VELOCITY", "MEDIUM", "MEDIUM",
             customers[15], branches[0].id, "RULE"),
            ("AL-2026-010", "Opération proche du seuil réglementaire", "THRESHOLD", "MEDIUM", "LOW",
             customers[17], branches[4].id, "RULE"),
            ("AL-2026-011", "Source de fonds inhabituelle", "SOURCE_OF_FUNDS", "MEDIUM", "MEDIUM",
             customers[2], branches[1].id, "RULE"),
            ("AL-2026-012", "Contrepartie commune multiple clients", "NETWORK", "HIGH", "HIGH",
             customers[4], None, "NETWORK"),
            ("AL-2026-013", "Nouveau bénéficiaire effectif", "KYC", "LOW", "LOW",
             customers[6], branches[2].id, "MANUAL"),
            ("AL-2026-014", "Retrait important compte dormant", "ACCOUNT_AGE", "MEDIUM", "MEDIUM",
             customers[8], branches[3].id, "RULE"),
            ("AL-2026-015", "Escalade conformité — cas 5", "ESCALATION", "CRITICAL", "HIGH",
             customers[10], None, "MANUAL"),
        ]
        alerts = []
        status_pool = ["NEW", "TO_REVIEW", "IN_PROGRESS", "PENDING", "ESCALATED",
                       "CONFIRMED", "DISMISSED", "CLOSED"]
        for code, title, src, sev, prio, cust, branch_id, alert_src in alert_defs:
            a = Alert(
                code=code, title=title, description=f"{title} — générée automatiquement",
                severity=sev, priority=prio,
                status=random.choice(status_pool),
                customer_id=cust.id, branch_id=branch_id,
                source=alert_src, created_by=users["responsable"].id,
                due_at=datetime.now() + timedelta(hours=random.choice([2, 6, 12, 24, 48])),
            )
            db.add(a)
            await db.flush()
            alerts.append(a)
            db.add(AlertEvent(alert_id=a.id, event_type="CREATED", user_id=users["responsable"].id))
        await db.flush()
        print(f"[seed] {len(alerts)} alertes OK")

        # Cas (5)
        for c in range(5):
            case = Case(
                code=f"CASE-2026-{c+1:03d}",
                title=f"Investigation {c+1}",
                description="Dossier d'investigation de conformité",
                status=random.choice(["OPEN", "IN_PROGRESS", "CLOSED"]),
                risk_level=random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                customer_id=customers[c * 3].id if c < 5 else None,
                assigned_to=users["responsable"].id,
                created_by=users["responsable"].id,
            )
            db.add(case)
            await db.flush()
            db.add(CaseNote(case_id=case.id, user_id=users["analyste"].id,
                            body="Analyse initiale du dossier"))
            db.add(CaseDecision(case_id=case.id, decision="NFA",
                                reason="Pas d'élément probant", decided_by=users["responsable"].id))
            if c < len(alerts):
                db.add(CaseAlert(case_id=case.id, alert_id=alerts[c].id))
        await db.flush()
        print("[seed] Cas OK")

        # ------------------------------------------------------------------
        # 10. Paramètres système (seuils de risque)
        # ------------------------------------------------------------------
        db.add(SystemSetting(key="risk_levels",
                             value=json.dumps({
                                 "LOW": [0, 29], "MEDIUM": [30, 59],
                                 "HIGH": [60, 79], "CRITICAL": [80, 100]}),
                             updated_by=users["admin"].id))
        # Config SLA
        db.add(SystemSetting(key="alert_sla_minutes",
                             value=json.dumps({"low": 1440, "medium": 720, "high": 360, "critical": 120}),
                             updated_by=users["admin"].id))
        # Conservation des journaux d'audit (jours) — purge périodique automatique
        db.add(SystemSetting(key="audit_log_retention_days",
                             value="365",
                             updated_by=users["admin"].id))
        await db.flush()

        # ------------------------------------------------------------------
        # 11. Relations réseau (Client A multi-caisses)
        # ------------------------------------------------------------------
        db.add(NetworkRelationship(relation_type="BENEFICIAL_OWNER_OF",
                                   from_type="CUSTOMER", from_id=client_a.id,
                                   to_type="CUSTOMER", to_id=customers[2].id))
        db.add(NetworkRelationship(relation_type="RELATED_TO",
                                   from_type="CUSTOMER", from_id=client_a.id,
                                   to_type="CUSTOMER", to_id=customers[2].id))
        await db.commit()
        print("[seed] Relations réseau OK")

        # ------------------------------------------------------------------
        # 12. Audit initial
        # ------------------------------------------------------------------
        db.add(AuditLog(
            actor_id=users["admin"].id, actor_role="superadmin",
            action="DATABASE_SEEDED", entity_type="SYSTEM",
            new_value=json.dumps({"clients": len(customers), "transactions": len(txns),
                                   "alertes": len(alerts)}),
            reason="Initialisation de la démonstration",
        ))
        await db.commit()

    print("[seed] Termine.")
    print("   Comptes de démonstration :")
    print("   • admin@cifguard.net  /  CIFGuard@2026   (superadmin)")
    print("   • reseau@cifguard.net /  CIFGuard@2026   (conformité réseau)")
    print("   • agent1@cifguard.net /  CIFGuard@2026   (agent caisse Dakar Plateau)")


if __name__ == "__main__":
    run_async(run())