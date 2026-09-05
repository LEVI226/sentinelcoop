# Matrice questions CIF et réponses solution

## Lecture des échanges terrain

Les sujets remontés par les interlocuteurs CIF montrent que le Topic 1 ne se limite pas à comparer un nom avec une liste. Le vrai besoin couvre le fonctionnement d'un réseau de caisses, la circulation des clients entre points de service, les opérations de caisse et la gouvernance des données.

## Matrice

| Sujet CIF | Risque métier | Réponse attendue dans la solution | Fichier de référence |
| --- | --- | --- | --- |
| Client avec comptes dans plusieurs caisses | Contournement par dispersion des opérations | `global_client_id`, solde global, cumul réseau | `06_modele_reseau_multi_caisses.md` |
| Dépôts et retraits | Flux suspects non détectés | Règles seuil, cumul, fractionnement, justification | `08_workflows_operations_caisse.md` |
| Création de compte | Entrée en relation à risque | KYC, CNIB, PPE, sanctions, bénéficiaire effectif | `08_workflows_operations_caisse.md` |
| Retrait par procuration | Tiers utilisé pour masquer le bénéficiaire réel | Mandat, validité, plafond, filtrage mandataire | `08_workflows_operations_caisse.md` |
| Seuils | Fractionnement ou absence de justificatif | Seuils par caisse et par zone | `catalogue_regles_alertes_topic1.csv` |
| Justification de fonds | Origine économique non documentée | Champ `origine_fonds`, justificatif, revue conformité | `modele_donnees_reseau_cif.csv` |
| Motifs d'opération | Libellés pauvres ou incohérents | Typologie des motifs, comparaison au profil | `02_donnees_importantes.md` |
| Produits financiers | Risque différent selon produit | `type_produit` et règles par produit | `modele_donnees_reseau_cif.csv` |
| Personne physique et morale | Bénéficiaire effectif absent | KYC différencié et champ bénéficiaire effectif | `modele_donnees_reseau_cif.csv` |
| Flux financiers | Vision locale insuffisante | Cumul client, compte, caisse, canal, période | `06_modele_reseau_multi_caisses.md` |
| KYC | Profil de risque incomplet | Score KYC explicable, pièces, activité, zone | `02_donnees_importantes.md` |
| Risque propre à chaque coopérative | Trop de faux positifs ou faux négatifs | Paramétrage local par zone et activité | `09_risque_geographique_et_parametrage_local.md` |
| Dori zone rouge | Risque FT et espèces plus élevé | Seuils abaissés, revue renforcée | `09_risque_geographique_et_parametrage_local.md` |
| Banfora zone stable | Contrôle proportionné | Seuil standard et comportement inhabituel | `09_risque_geographique_et_parametrage_local.md` |
| Délai de filtrage | Sanction appliquée trop tard | Filtrage immédiat, cache liste, alerte liste obsolète | `09_risque_geographique_et_parametrage_local.md` |
| Interopérabilité réseau | Caisses isolées | Signal réseau minimal et pseudonymisé | `06_modele_reseau_multi_caisses.md` |
| Anonymisation | Exposition excessive des clients | Pseudonymisation et minimisation | `07_rbac_anonymisation_visibilite.md` |
| Visibilité différenciée | Tous voient trop de données | RBAC par rôle et périmètre | `07_rbac_anonymisation_visibilite.md` |
| Validité CNIB | Opération avec pièce expirée | Règle bloquante CNIB expirée | `catalogue_regles_alertes_topic1.csv` |
| Carnet bancaire/caisse | Décalage papier/digital | Référence carnet et rapprochement | `08_workflows_operations_caisse.md` |
| Formulaire de retrait | Données incomplètes | Champs obligatoires et preuve de validation | `08_workflows_operations_caisse.md` |

## Ce que cela change dans le MVP

Le MVP doit démontrer quatre capacités:

- identifier un client au niveau réseau sans exposer toutes ses données;
- contrôler les opérations de caisse avec règles locales;
- gérer les alertes dans un workflow conformité;
- prouver la traçabilité par audit trail.

## Démo recommandée

1. Créer deux caisses: Dori en zone rouge et Banfora en zone verte.
2. Créer un même client avec deux comptes dans deux caisses.
3. Simuler un dépôt fractionné à Dori.
4. Simuler un retrait par procuration avec mandat proche de l'expiration.
5. Montrer l'alerte informative puis l'alerte bloquante.
6. Basculer en rôle conformité réseau pour voir le risque consolidé.
7. Montrer qu'un agent de Banfora ne voit pas les détails confidentiels de Dori.
8. Exporter le journal d'audit.
