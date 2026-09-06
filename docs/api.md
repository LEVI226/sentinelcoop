# API — CIF Guard Backend

Préfixe : `/api/v1`. Documentation interactive : `/api/docs` (Swagger UI).

Format success : `{ "success": true, "data": {...}, "meta": { "requestId": "..." } }`
Format erreur  : `{ "success": false, "error": { "code", "message", "details" }, "requestId" }`

Authentification : `Authorization: Bearer <access>`. Comptes démo (mot de passe
`CIFGuard@2026`) : `admin@cifguard.net`, `reseau@cifguard.net`, `agent1@cifguard.net`.

## Auth (`/auth`)
| Méthode | Route | Description |
|---|---|---|
| POST | `/auth/login` | Connexion (email + mot de passe) |
| POST | `/auth/refresh` | Rotation refresh token → nouveau access + refresh |
| POST | `/auth/logout` | Déconnexion |
| GET | `/auth/me` | Profil + rôles + permissions |
| POST | `/auth/change-password` | Changer le mot de passe |
| POST | `/auth/recover` | Demande de récupération |
| GET/DELETE | `/auth/sessions[/{id}]` | Lister / révoquer les sessions |

## Clients & KYC (`/customers`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST | `/customers` | Lister (recherche par blind index `?query=`) / créer |
| GET/PATCH | `/customers/{id}` | Détail (PII déchiffrées si ABAC) / modifier |
| GET | `/customers/{id}/risk` | Score + historique + explication |
| GET | `/customers/{id}/accounts|transactions|alerts|cases|history` | Sous-ressources |
| POST | `/customers/{id}/screen` | Lancer un screening (→ `ScreeningRun` + `ScreeningMatch`) |
| POST | `/customers/{id}/review` | Revue conformité |
| PATCH | `/customers/{id}/kyc` (misc) | Mettre à jour le KYC / PEP + recompute risque |

## Transactions (`/transactions`)
| Méthode | Route | Description |
|---|---|---|
| POST | `/transactions` | Enregistrer une transaction (analyse async) |
| GET | `/transactions` | Lister (+ filtres status / risk) |
| GET | `/transactions/{id}` | Détail |

## Comptes (`/accounts`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST | `/accounts` | Lister / créer |
| GET/PATCH | `/accounts/{id}` | Détail + transactions récentes / modifier |
| GET | `/accounts/{id}/transactions` | Historique |

## Alertes (`/alerts`) — workflow SLA
| Méthode | Route | Description |
|---|---|---|
| GET/POST | `/alerts` | Lister / créer |
| GET/PATCH | `/alerts/{id}` | Détail / modifier |
| POST | `/alerts/{id}/assign|escalate|comment|request-information|confirm|dismiss|close` | Workflow |

## Dossiers (`/cases`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST | `/cases` | Lister / créer (rattache alertes) |
| GET/PATCH | `/cases/{id}` | Détail agrégé / modifier |
| POST | `/cases/{id}/alerts|transactions|notes|tasks|decision|close` | Workflow d'investigation |

## Règles (`/rules`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST | `/rules` | Lister / créer (avec version initiale) |
| GET/PATCH | `/rules/{id}` | Détail + versions / modifier |
| POST | `/rules/{id}/activate|deactivate` | Activer / désactiver |
| GET | `/rules/{id}/versions` | Historique des versions |

## Screening (`/screening`)
| Méthode | Route | Description |
|---|---|---|
| GET | `/screening/matches` | Correspondances |
| GET | `/screening/runs` | Exécutions |
| GET | `/screening/list-versions[/{id}]` | Versions des listes (et preview entités) |
| POST | `/screening/lists/import` | Importer une liste (checksum SHA-256, versionné) |
| GET | `/screening/lists/status` | Fraîcheur des listes |

## Déclarations & filtrage (`/declarations`, `/filtering-results`)
| Méthode | Route | Description |
|---|---|---|
| POST/GET/PATCH | `/declarations[/{id}]` | Déclarations de soupçon |
| GET | `/filtering-results` | Résultats de filtrage |
| POST | `/filtering-results/{id}/decision` | Décision sur un résultat |

## Tableau de bord (`/dashboard`)
| Méthode | Route | Description |
|---|---|---|
| GET | `/dashboard/summary` | KPIs (clients, risque, alertes, transactions) |
| GET | `/dashboard/risk-distribution` | Répartition par niveau |
| GET | `/dashboard/alerts-trend` | Volume sur N jours |
| GET | `/dashboard/priority-alerts` | Alertes critiques |
| GET | `/dashboard/transaction-summary` | Synthèse volumes |
| GET | `/dashboard/compliance-summary` | KYC / screening / dossiers / déclarations |

## Organisation (`/cooperatives`, `/branches`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST/PATCH | `/cooperatives[/{id}]` | Coopératives |
| GET/POST/PATCH | `/branches[/{id}]` | Caisses (détail + profil de risque) |
| POST | `/branches/{id}/risk-profile` | Mettre à jour le profil de risque de caisse |

## Utilisateurs & rôles (`/users`, `/roles`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST/PATCH | `/users[/{id}]` | Utilisateurs |
| GET | `/roles` | Rôles + permissions |

## Réseau (`/network`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST | `/network/relationships` | Relations réseau |
| GET | `/network/customers/{id}` | Graphe réseau d'un client (multi-caisses) |
| GET | `/network/identities` | Identités pseudonymisées |
| POST | `/network/identities/match` | Déclarer une correspondance |

## Audit (`/audit`)
| Méthode | Route | Description |
|---|---|---|
| GET | `/audit` | Journal (filtres entity/action/actor, pagination) |
| GET | `/audit/summary` | Agrégats par action |

## Divers (`/info`, `/documents`, `/attachments`, `/reports`, `/notifications`, `/sync`, `/settings`)
| Méthode | Route | Description |
|---|---|---|
| GET/POST/PATCH | `/information-requests[/{id}]` | Demandes d'information |
| GET | `/documents`, `/attachments` | Documents / pièces jointes |
| POST/GET | `/reports` | Génération / liste des rapports |
| GET/POST | `/notifications[/{id}/read]` | Notifications |
| POST | `/sync/events` | Push d'événements hors-ligne (idempotent par `event_id`) |
| GET | `/sync/status` | Statut de synchronisation |
| GET/PUT | `/settings` | Paramètres système |

## Système
| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/health/database` | Connectivité base |
| GET | `/` | Info service |
