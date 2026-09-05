# RBAC, anonymisation et visibilité des données

## Objectif

Tout le monde ne doit pas voir le même niveau de détail sur les données clientes. La solution doit appliquer une logique de moindre privilège: chaque utilisateur accède uniquement aux informations nécessaires à son rôle.

## Rôles recommandés

| Rôle | Périmètre | Droits principaux |
| --- | --- | --- |
| Agent de caisse | Sa caisse | Créer client, saisir opération, voir alertes de saisie |
| Chef de caisse | Sa caisse | Valider certaines opérations, consulter activité locale |
| Responsable conformité caisse | Sa caisse | Traiter alertes locales, demander justificatifs, escalader |
| Responsable conformité réseau | Réseau CIF | Voir risques consolidés, cas multi-caisses, alertes critiques |
| Auditeur interne | Réseau ou mission | Lire journaux, preuves, décisions, sans modifier |
| Administrateur fonctionnel | Paramétrage | Gérer seuils, listes, rôles, caisses |
| Superviseur externe | Sur demande | Exports réglementaires et preuves autorisées |

## Niveaux de visibilité

| Donnée | Agent caisse | Conformité caisse | Conformité réseau | Audit |
| --- | --- | --- | --- | --- |
| Nom client local | Oui | Oui | Masqué sauf alerte critique | Selon mission |
| Pièce d'identité | Oui si saisie | Oui | Masquée par défaut | Selon mission |
| Autres comptes du réseau | Indicateur seulement | Indicateur et risque | Oui avec minimisation | Selon mission |
| Solde global réseau | Non | Oui si alerte | Oui | Oui |
| Historique transactions local | Oui | Oui | Agrégé par défaut | Oui |
| Transactions autres caisses | Non | Agrégé si nécessaire | Oui selon habilitation | Oui |
| Alertes sanctions | Oui si bloquante | Oui | Oui | Oui |
| Paramétrage seuils | Non | Lecture | Lecture | Lecture |

## Pseudonymisation

Le `global_client_id` doit être calculé ou attribué sans exposer directement l'identité complète. Pour le hackathon, on peut simuler cette logique:

- `global_client_id = hash(nom_normalise + date_naissance + pays + sel_reseau)`
- conservation du nom complet seulement dans la caisse d'origine;
- partage réseau limité aux scores, indicateurs et statuts;
- export démo sans données personnelles réelles.

## Anonymisation pour la démo

La démo doit utiliser uniquement:

- clients fictifs;
- pièces d'identité fictives;
- numéros de comptes fictifs;
- listes sanctions/PPE synthétiques;
- transactions simulées;
- villes et caisses réalistes mais sans client réel.

## Contrôles d'accès à montrer

- Connexion par rôle.
- Filtrage des écrans selon le rôle.
- Masquage partiel des champs sensibles.
- Journalisation des consultations sensibles.
- Journalisation des modifications de seuils et listes.
- Export conformité réservé aux rôles autorisés.

## Risque à éviter

Ne pas construire une démo où tout le monde voit tous les clients du réseau. Le jury CIF a explicitement soulevé la question de la visibilité différenciée. Une bonne réponse GRC doit montrer une séparation claire entre donnée locale, signal réseau et accès conformité.
