# Specs - Demo SentinelleCoop

## Architecture

Application web statique:

- `index.html`: structure et contrat de direction;
- `styles.css`: systeme visuel et responsive;
- `app.js`: donnees, logique de scoring demo, rendu et interactions;
- `test-demo.js`: tests rapides de logique metier.

Le prototype Python reste la reference technique du moteur. La demo web reproduit les resultats essentiels avec des donnees synthetiques pour rendre le pitch fluide.

## Navigation

La demo contient quatre vues:

- Filtrage
- Transactions
- Alertes
- Audit

Chaque vue doit etre accessible sans rechargement de page.

## Filtrage Client

Champs:

- nom du client;
- type de client;
- agence.

Resultat:

- meilleur match;
- score;
- decision: bloquant, informatif ou conforme;
- raisons lisibles: variante detectee, source, similarite.

Cas demo prioritaire:

- `Djallo Mamadou` doit declencher une alerte forte liee a `Diallo Mamadou`.

## Transactions

Donnees:

- clients;
- comptes;
- soldes;
- transactions.

Regles:

- consolidation du solde global par client;
- cumul des operations sur 7 jours;
- alerte fractionnement si plusieurs operations proches restent sous seuil mais depassent un total configure;
- alerte compte rebond si reception puis transfert rapide vers un autre compte.

## Alertes

Chaque alerte a:

- severite;
- type;
- client;
- montant ou score;
- motif;
- statut;
- action de decision.

Actions:

- confirmer;
- lever;
- escalader.

Chaque action ajoute une entree d'audit.

## Audit

Afficher:

- age des listes;
- derniere synchronisation;
- source des listes;
- nombre d'alertes;
- journal des decisions;
- bouton d'export rapport.

## Tests

Les tests doivent verifier:

- matching `Djallo Mamadou` -> alerte;
- score faible pour un nom sans rapport;
- consolidation multi-comptes;
- detection de fractionnement;
- ajout d'une entree d'audit apres decision.

