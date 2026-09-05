# Modèle réseau CIF multi-caisses

## Problème métier

Le réseau CIF regroupe plusieurs structures et caisses. Un même client peut détenir plusieurs comptes dans différentes caisses. Pour la conformité LBC/FT/FP, l'analyse ne doit donc pas rester bloquée au niveau d'un seul compte ou d'une seule caisse.

Le bon modèle sépare:

- la personne ou entité cliente;
- les comptes;
- les caisses/agences;
- les opérations;
- les mandats et procurations;
- les alertes conformité;
- les décisions humaines.

## Principe clé

Un compte appartient à une caisse, mais le risque appartient au client consolidé.

Exemple:

- Client C001 détient un compte épargne à Dori.
- Le même client détient un compte courant à Ouagadougou.
- Il effectue plusieurs dépôts dans une caisse et des retraits dans une autre.
- Le système doit consolider l'exposition client au niveau réseau, même si chaque caisse ne voit qu'une partie autorisée des données.

## Identifiants recommandés

| Objet | Identifiant | Usage |
| --- | --- | --- |
| Client réseau | `global_client_id` | Identifiant pseudonymisé commun au réseau |
| Client local caisse | `local_client_id` | Identifiant interne à la caisse |
| Caisse | `caisse_id` | Point de service ou institution membre |
| Compte | `compte_id` | Compte ouvert dans une caisse |
| Opération | `operation_id` | Dépôt, retrait, virement, retrait par procuration |
| Procuration | `mandat_id` | Autorisation donnée à un tiers |
| Alerte | `alerte_id` | Cas conformité |

## Consolidation multi-comptes

Le système doit calculer:

- le nombre de comptes par client;
- le solde par compte;
- le solde global du client;
- les dépôts cumulés par période;
- les retraits cumulés par période;
- les flux entre caisses;
- les opérations effectuées par mandataire;
- les opérations atypiques par rapport au profil.

## Vue caisse et vue réseau

| Vue | Ce qui est visible | Ce qui est masqué |
| --- | --- | --- |
| Agent de caisse | Client local, opération locale, alerte locale | Données détaillées des autres caisses |
| Responsable conformité caisse | Alertes de sa caisse, historique local, indicateurs consolidés minimaux | Identité complète hors périmètre |
| Conformité réseau | Risque consolidé, multi-comptes, alertes croisées | Données opérationnelles non nécessaires |
| Audit | Journaux, décisions, preuves, versions de listes | Accès selon mandat d'audit |

## Interopérabilité réseau

Le système doit permettre l'échange minimal de signaux entre caisses:

- identifiant pseudonymisé du client;
- indicateur multi-comptes;
- score de risque consolidé;
- liste d'alertes ouvertes;
- statut PPE ou sanction si applicable;
- date de dernière mise à jour KYC;
- version de liste utilisée pour le filtrage.

Il ne faut pas partager toutes les données nominatives avec tout le réseau. Le partage doit suivre le besoin d'en connaître.

## Architecture recommandée

### Option MVP hackathon

- Base locale SQLite par caisse.
- Fichier de synchronisation JSON chiffrable ou pseudonymisé.
- Index réseau simulé avec `global_client_id`.
- Tableau de bord conformité réseau en lecture limitée.

### Option cible déployable

- Référentiel central des identités pseudonymisées.
- Connecteurs vers les systèmes de caisse.
- API de filtrage commune.
- Journal d'audit central.
- Gestion des habilitations par rôle et périmètre.

## Message à défendre au jury

La solution respecte la réalité d'un réseau: chaque caisse garde son autonomie opérationnelle, mais la conformité dispose d'une vision consolidée suffisante pour détecter les risques multi-comptes, les contournements de seuils et les flux inhabituels.
