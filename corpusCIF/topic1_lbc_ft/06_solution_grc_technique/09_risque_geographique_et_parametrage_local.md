# Risque géographique et paramétrage local

## Principe

Chaque coopérative n'a pas le même profil de risque. Une caisse située dans une zone sécuritaire sensible doit appliquer une vigilance différente d'une caisse située dans une zone stable.

Exemple de cadrage:

- Dori: zone rouge ou zone de sécurité sensible.
- Banfora: zone plus stable dans l'exemple donné.

Le système doit permettre un paramétrage local sans casser les règles réseau.

## Table de risque local

| Zone | Niveau | Effet sur les contrôles |
| --- | --- | --- |
| Zone verte | Faible | Seuils standards, revue normale |
| Zone orange | Moyen | Seuils abaissés, justificatif plus fréquent |
| Zone rouge | Élevé | Revue renforcée, alertes plus sensibles, suivi des espèces |

## Paramètres par caisse

- niveau de risque géographique;
- activités économiques dominantes;
- produits proposés;
- seuils dépôts/retraits;
- seuils de cumul;
- délai maximal de revue d'alerte;
- fréquence de mise à jour des listes;
- mode de synchronisation.

## Règles adaptées au lieu

### Dori ou zone rouge

- Seuil de justification des dépôts plus bas.
- Contrôle renforcé sur dépôts en espèces.
- Revue plus stricte des retraits par procuration.
- Surveillance du cumul multi-comptes.
- Score de risque augmenté pour activités sensibles.
- Délai de traitement plus court pour alerte critique.

### Banfora ou zone plus stable

- Seuils standards.
- Revue renforcée déclenchée par comportement inhabituel plutôt que par zone seule.
- Contrôle des gros montants et fractionnements.
- Surveillance normale des procurations.

## Délai de filtrage

Le système doit distinguer:

- filtrage immédiat à la création client;
- filtrage immédiat avant opération si liste locale disponible;
- revue différée si faible connectivité et alerte informative;
- blocage local si forte similarité sanction;
- alerte si les listes n'ont pas été mises à jour depuis trop longtemps.

## Proposition de SLA

| Type d'alerte | Délai cible |
| --- | --- |
| Sanction forte | Blocage immédiat |
| PPE | Revue conformité avant validation complète |
| CNIB expirée | Blocage ou régularisation immédiate |
| Dépôt au-dessus seuil | Justificatif avant clôture |
| Fractionnement suspect | Revue sous 24 heures |
| Liste obsolète | Alerte administrateur dès dépassement du délai |

## Message au jury

La solution applique une approche fondée sur les risques. Elle ne traite pas toutes les caisses comme si elles avaient le même contexte. Le paramétrage local améliore la pertinence des alertes et limite les faux positifs.
