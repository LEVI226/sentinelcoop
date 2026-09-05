# Architecture bancaire cible - Topic 1 CIF

## Hypothèse de départ

La CIF est un réseau de caisses et structures membres. La solution doit donc traiter un volume significatif de clients, comptes et transactions, tout en restant déployable dans des environnements hétérogènes: caisses urbaines bien connectées, caisses rurales avec connectivité faible, postes Windows, terminaux Android et systèmes existants différents.

Le bon schéma n'est pas une application isolée. C'est une plateforme légère de conformité réseau, capable de fonctionner localement et de synchroniser des signaux utiles vers un niveau central.

## Architecture en deux niveaux

### Niveau caisse

Le niveau caisse doit continuer à fonctionner même avec une connexion instable.

Composants:

- interface agent;
- base locale;
- moteur local de filtrage;
- cache local des listes sanctions/PPE;
- journal local des opérations;
- file de synchronisation.

### Niveau réseau

Le niveau réseau consolide les signaux sans exposer inutilement toutes les données nominatives.

Composants:

- référentiel pseudonymisé client réseau;
- API conformité;
- moteur d'analyse consolidée;
- supervision des alertes critiques;
- gestion des listes;
- audit trail central;
- exports conformité.

## Schéma logique

```text
Terminaux caisse
Android / Windows / navigateur
        |
        v
Application caisse légère
PWA ou web local
        |
        v
API locale ou API régionale
        |
        +-- SQLite local caisse
        +-- Cache listes sanctions/PPE
        +-- Moteur filtrage noms
        +-- Moteur règles opérations
        +-- Journal audit local
        +-- File sync sortante
        |
        v
Passerelle interopérabilité
REST / JSON / CSV batch
        |
        v
Plateforme conformité réseau
        |
        +-- Référentiel client pseudonymisé
        +-- Consolidation multi-comptes
        +-- Alertes réseau
        +-- Gestion versions listes
        +-- Reporting et audit
```

## Stack MVP hackathon

| Couche | Choix recommandé | Raison |
| --- | --- | --- |
| Frontend | React + Vite + TypeScript | Rapide, responsive, maintenable |
| UI | CSS simple ou Tailwind | Léger, productif |
| Backend | FastAPI Python | API claire, OpenAPI, logique métier simple |
| Base | SQLite | Offline, zéro serveur, facile à embarquer |
| Import données | CSV | Compatible terrain et hackathon |
| Sync | JSON files + endpoint REST | Simple à démontrer |
| Matching noms | Module `sentinellecoop` | Adapté aux variantes ouest-africaines |
| Audit | Table SQLite append-only | Traçabilité démontrable |
| Déploiement | Localhost ou LAN | Réaliste pour 72h |

## Stack cible production

| Couche | Choix cible | Raison |
| --- | --- | --- |
| Frontend | PWA React ou Angular | Déploiement central, usage Android/Windows |
| API | FastAPI, NestJS ou Spring Boot | Selon SI existant et compétences internes |
| Base caisse | SQLite chiffré ou PostgreSQL local | Mode dégradé et autonomie caisse |
| Base centrale | PostgreSQL | Transactions, audit, reporting |
| Cache | Redis | Listes, sessions, files courtes |
| Event streaming | Kafka, Redpanda ou RabbitMQ | Flux transactionnels réseau |
| Recherche noms | PostgreSQL trigram + moteur phonétique | Performance et explicabilité |
| IAM | Keycloak ou IAM existant | RBAC, SSO, traçabilité |
| Observabilité | OpenTelemetry + Prometheus/Grafana | Suivi technique |
| Secrets | Vault ou secret manager | Clés et paramètres sensibles |
| Déploiement | Docker Compose puis Kubernetes | Progression simple vers échelle réseau |

## Schéma de données central

```text
caisse
  caisse_id
  ville
  pays
  niveau_risque_zone
  seuils locaux

client_local
  local_client_id
  caisse_id
  global_client_id
  données nominatives locales
  statut KYC

client_reseau
  global_client_id
  hash_identite
  score_risque_consolide
  indicateur_multi_caisses
  dernière_revue_kyc

compte
  compte_id
  global_client_id
  caisse_id
  type_produit
  solde
  statut

operation
  operation_id
  compte_id
  caisse_id
  type_operation
  montant
  canal
  motif
  origine_fonds
  justificatif_id

mandat_procuration
  mandat_id
  global_client_id
  mandataire_hash
  validité
  plafond
  statut

watchlist_entry
  liste_id
  type_liste
  nom_normalise
  alias
  version_liste
  criticite

alerte
  alerte_id
  operation_id
  global_client_id
  type_alerte
  niveau
  score
  statut
  decision

audit_log
  audit_id
  acteur
  role
  action
  objet
  horodatage
  empreinte
```

## Flux temps réel et batch

### Flux création client

```text
Saisie KYC
  -> validation champs obligatoires
  -> contrôle CNIB
  -> normalisation nom
  -> filtrage sanctions/PPE local
  -> création client local
  -> génération global_client_id pseudonymisé
  -> synchronisation signal réseau
  -> audit log
```

### Flux opération

```text
Saisie opération
  -> contrôle seuil local
  -> contrôle procuration si applicable
  -> filtrage contrepartie si applicable
  -> calcul cumul client
  -> calcul risque zone
  -> génération alerte
  -> décision agent ou conformité selon niveau
  -> audit log
  -> sync différée ou immédiate
```

### Flux mise à jour sanctions/PPE

```text
Import liste centrale
  -> validation format
  -> versioning
  -> diffusion aux caisses
  -> cache local
  -> alerte si caisse non synchronisée
  -> filtrage rétroactif optionnel des clients actifs
```

## Performance et légèreté

### Optimisations MVP

- Charger les listes sanctions/PPE en mémoire au démarrage.
- Pré-normaliser les noms et alias.
- Créer un index phonétique pour éviter de comparer tous les noms.
- Stocker les opérations dans SQLite avec index sur `global_client_id`, `compte_id`, `date_operation`, `caisse_id`.
- Calculer les cumuls par fenêtres simples: 24h, 7 jours, 30 jours.
- Limiter les écrans à ce que l'utilisateur doit voir.

### Index SQLite recommandés

```sql
CREATE INDEX idx_operations_client_date ON operations(global_client_id, date_operation);
CREATE INDEX idx_operations_compte_date ON operations(compte_id, date_operation);
CREATE INDEX idx_operations_caisse_date ON operations(caisse_id, date_operation);
CREATE INDEX idx_comptes_client ON comptes(global_client_id);
CREATE INDEX idx_alertes_statut ON alertes(statut, niveau);
CREATE INDEX idx_watchlist_phonetic ON watchlist_entries(code_phonetique);
```

### Optimisations cible production

- Traitement événementiel pour transactions.
- Partitionnement par caisse et mois pour les opérations.
- Matérialisation des agrégats client: solde global, cumul 7j, cumul 30j.
- Cache des scores de matching.
- Refiltrage asynchrone après mise à jour de liste.
- Files de priorité pour alertes bloquantes.

## Interopérabilité avec systèmes existants

La solution ne doit pas imposer un remplacement du SI caisse. Elle doit s'interfacer.

Modes d'intégration:

- import CSV quotidien;
- dépôt de fichiers JSON;
- API REST;
- webhook transactionnel;
- connecteur base de données en lecture;
- export réglementaire.

Contrat minimal d'une opération:

```json
{
  "operation_id": "OP_001",
  "caisse_id": "CAISSE_DORI",
  "compte_id": "CPT_DOR_001",
  "global_client_id": "GCLI_001",
  "type_operation": "depot",
  "montant": 240000,
  "date_operation": "2026-09-05T08:30:00",
  "canal": "guichet",
  "motif": "vente betail",
  "origine_fonds": "recette marche"
}
```

## Sécurité et gouvernance

### Principes

- Moindre privilège.
- Pseudonymisation réseau.
- Traçabilité append-only.
- Séparation saisie et décision conformité.
- Chiffrement des exports sensibles.
- Versioning des listes.

### RBAC minimal

| Rôle | Pouvoir |
| --- | --- |
| Agent caisse | Saisie locale, alertes de saisie |
| Chef caisse | Validation locale limitée |
| Conformité caisse | Revue alertes locales |
| Conformité réseau | Vue consolidée et alertes critiques |
| Admin | Paramètres et listes |
| Audit | Lecture journaux et exports |

## Résilience faible connectivité

La caisse doit continuer à:

- créer des clients;
- filtrer avec la dernière liste locale;
- saisir des opérations;
- générer des alertes locales;
- stocker les décisions;
- synchroniser plus tard.

Le système doit afficher:

- date de dernière synchronisation;
- version de liste locale;
- nombre d'événements en attente;
- statut de synchronisation.

## Niveaux de déploiement

### Niveau 1 - Hackathon

- Une machine développeur.
- Frontend local.
- API FastAPI.
- SQLite.
- CSV synthétiques.

### Niveau 2 - Pilote caisse

- Mini serveur local ou poste Windows.
- Plusieurs profils utilisateurs.
- Import CSV depuis SI caisse.
- Synchronisation réseau planifiée.

### Niveau 3 - Réseau CIF

- Plateforme centrale.
- API interopérabilité.
- Consolidation multi-caisses.
- Monitoring.
- Reporting conformité.

## Ce qu'il faut montrer dans la démo

- La solution tourne vite sur une machine simple.
- Le filtrage ne dépend pas d'Internet.
- Dori et Banfora n'ont pas les mêmes seuils.
- Un client multi-caisses génère une vue risque consolidée.
- Un retrait par procuration expirée bloque.
- Un agent ne voit pas toute la donnée réseau.
- La conformité réseau voit les signaux nécessaires.
- Chaque décision laisse une trace.

## Phrase d'architecture pour le pitch

Nous proposons une plateforme de conformité réseau légère: chaque caisse garde un fonctionnement local et hors ligne, tandis que le niveau CIF consolide uniquement les signaux nécessaires pour détecter les risques multi-comptes, sanctions, PPE, seuils et procurations.
