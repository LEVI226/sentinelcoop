# Mapping diagramme de classes LBC/FT ↔ Modèles implémentés

Transcription du `diagramme_classes_filtre_LBC_FT.md` (fourni le 2026-09-06).
Les classes du diagramme sont mises en regard des modèles SQLAlchemy du backend.

## Correspondance des classes

| Classe (diagramme) | Table / Modèle | Notes |
|---|---|---|
| `InstitutionFinanciere` | `cooperatives` + `branches` | Caisse du réseau CIF |
| `Client` | `customers` | PII chiffrées AES-256-GCM |
| `ClientParticulier` | `customers.customer_type='INDIVIDUAL'` | Héritage → champ discriminé |
| `ClientMorale` | `customers.customer_type='COMPANY'` + `customer_beneficial_owners` | BE gérés à part |
| `CompteClient` | `accounts` + `account_holders` | |
| `Transaction` | `transactions` | `counterparty_id` = contrepartie |
| `TypeOperation` | `transactions.type` (enum) | DEPOSIT/WITHDRAWAL/TRANSFER/... |
| `RegleDetection` | `rules` + `rule_versions` + `rule_conditions/actions` | Versionné |
| `Alerte` | `alerts` | `alert_type` = TypeAlerte |
| `TypeAlerte` | `alerts.alert_type` | SECURITE / CONFORMITE / INFORMATIVE |
| `StatutAlerte` | `alerts.status` | NOUVELLE→NEW, EN_COURS→IN_PROGRESS, etc. |
| `ListeSanction` | `screening_lists` + `screening_list_versions` + `screening_entities` | Versionné |
| `ResultatFiltrage` | `resultats_filtrage` (+ `screening_runs`/`screening_matches`) | |
| `DeclarationSoupcon` | `declaration_soupcons` | À destination de l'autorité (CENTIF) |
| `AgentConformite` | `users` (rôle `conformite_reseau`/`analyste_conformite`) | |
| `JournalAudit` | `audit_logs` | append-only |

## Correspondance des relations

| Relation (diagramme) | Implémentation |
|---|---|
| InstitutionFinanciere → Client | `customers.branch_id → branches.id` (→ cooperative) |
| InstitutionFinanciere → CompteClient | `accounts.branch_id → branches.id` |
| Client → ClientParticulier / ClientMorale | champ `customer_type` |
| Client → CompteClient | `accounts.customer_id → customers.id` |
| CompteClient → Transaction | `transactions.account_id → accounts.id` |
| Transaction → TypeOperation | enum `transactions.type` |
| RegleDetection → Alerte | `alerts.rule_id → rules.id` |
| Alerte → TypeAlerte | champ `alerts.alert_type` |
| Alerte → StatutAlerte | champ `alerts.status` |
| Alerte → ResultatFiltrage | `resultats_filtrage.transaction_id` (lien via transaction) |
| ListeSanction → ResultatFiltrage | `resultats_filtrage.liste_id → screening_lists.id` |
| ResultatFiltrage → DeclarationSoupcon | `declaration_soupcons.transaction_id` |
| AgentConformite → DeclarationSoupcon | `declaration_soupcons.declare_par → users.id` |
| AgentConformite → JournalAudit | `audit_logs.actor_id → users.id` |
| Transaction → Alerte | `alerts.transaction_id → transactions.id` |

## Statuts d'alerte — équivalence

| Diagramme (français) | Implémentation (code) |
|---|---|
| NOUVELLE | `NEW` |
| EN_COURS | `IN_PROGRESS` |
| TRAITEE | `CONFIRMED` / `CLOSED` |
| ESCALADE | `ESCALATED` |
| CLOTUREE | `CLOSED` |

> Les codes implémentés sont alignés sur le CDC CIF Guard (§21) ; le diagramme
> français reste compréhensible via cette table d'équivalence.