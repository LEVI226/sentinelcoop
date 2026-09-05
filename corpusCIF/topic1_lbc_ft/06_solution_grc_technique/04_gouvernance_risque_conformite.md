# Gouvernance, risque et conformité

## Positionnement GRC

La solution doit être présentée comme un dispositif d'aide à la conformité. Elle ne doit pas prétendre prendre seule les décisions sensibles. Le bon positionnement: automatiser le filtrage, prioriser les alertes, documenter les décisions et faciliter l'escalade.

## Rôles

- Agent de caisse: saisit client ou transaction, voit uniquement les alertes nécessaires.
- Responsable conformité SFD: traite les alertes, qualifie les faux positifs, escalade.
- Administrateur: gère les seuils, les listes, les profils et les droits.
- Audit/inspection: consulte les journaux, exports et preuves.

## Contrôles clés

- Séparation des rôles entre saisie opérationnelle et décision conformité.
- Journalisation des alertes, décisions, changements de seuils et mises à jour de listes.
- Traçabilité des versions des listes sanctions/PPE.
- Justification obligatoire pour fermer une alerte.
- Export des alertes pour revue ou reporting.
- Conservation minimale des preuves de traitement.
- Contrôle d'accès par profil.
- Masquage des données sensibles dans les écrans non nécessaires.

## Registre des risques

| Risque | Impact | Mesure de maîtrise |
| --- | --- | --- |
| Faux négatif sur liste de sanctions | Client à risque non détecté | Matching approximatif, alias, seuils prudents, revue des scores limites |
| Faux positif excessif | Saturation conformité | Score explicable, tri par criticité, clôture documentée |
| Liste obsolète | Sanction non appliquée à temps | Cache horodaté, import manuel, alerte si liste trop ancienne |
| Faible connectivité | Filtrage impossible | Mode local, synchronisation différée |
| Données personnelles réelles en démo | Exclusion ou perte de confiance | Dataset synthétique, README explicite |
| Décision automatisée non contrôlée | Risque réglementaire | Validation humaine obligatoire pour escalade |
| Modification non autorisée des seuils | Contournement du contrôle | Droits admin, journal d'audit |

## Indicateurs à présenter

- Nombre d'alertes générées.
- Part des alertes bloquantes.
- Temps moyen de revue.
- Taux de faux positifs sur scénario de test.
- Dernière mise à jour des listes.
- Nombre de clients multi-comptes détectés.
- Montant cumulé par client sur période.

## Message de pitch GRC

La solution aide un SFD à passer d'un contrôle manuel fragile à un contrôle traçable, paramétrable et adapté aux faibles moyens informatiques. Elle prouve au jury que l'équipe comprend les obligations LBC/FT/FP autant que la réalité opérationnelle des caisses.
