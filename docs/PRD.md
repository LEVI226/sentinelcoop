# PRD - SentinelleCoop Demo Hackathon

## Objectif

Transformer le prototype phonetic existant en demonstration metier complete pour le Hackathon CIF DigiCoop-WA+ Burkina Faso, du 4 au 6 septembre 2026.

La demo doit convaincre le jury que SentinelleCoop peut devenir un pilote CIF rapidement, parce qu'elle repond aux contraintes du TDR: filtrage client, filtrage transactionnel, alertes bloquantes/informatives, solde global multi-comptes, operations suspectes, sanctions ciblees sans delai, connectivite limitee et faibles ressources informatiques.

## Utilisateurs

- Agent de guichet: saisit un client ou une transaction et comprend immediatement quoi faire.
- Responsable conformite: revise les alertes, motive les decisions et produit les actes.
- Jury CIF: evalue la pertinence, l'innovation, la faisabilite et l'impact.

## Probleme

Les cooperatives financieres doivent filtrer clients et transactions, mais les outils classiques sont chers, connectes en permanence, et peu adaptes aux noms ouest-africains. Les controles manuels exposent l'institution et les agents a des erreurs, des retards et une preuve insuffisante devant controle.

## Proposition

SentinelleCoop est une application locale, offline-first, qui:

- filtre les clients contre un referentiel de sanctions;
- detecte les variantes de noms ouest-africains;
- distingue alertes bloquantes et informatives;
- consolide plusieurs comptes appartenant au meme client;
- detecte le fractionnement par cumul d'operations;
- garde une piste d'audit horodatee;
- prepare un rapport de conformite.

## Portee MVP Demo

Inclus pour la demo:

- ecran Filtrage client;
- ecran Transactions;
- ecran Alertes;
- ecran Audit;
- donnees synthetiques de cooperative;
- benchmark resume du moteur;
- generation de rapport texte;
- fonctionnement sans dependance externe.

Hors portee pour la demo:

- integration core banking reelle;
- ingestion automatique UE/OFAC;
- authentification production;
- chiffrement complet;
- vrai connecteur CENTIF;
- calibrage statistique sur portefeuille reel.

## Critere de succes

Pendant un pitch de 4 minutes, le jury doit voir:

1. un cas de nom ouest-africain que Soundex rate ou traite mal;
2. une alerte claire avec decision bloquante/informative;
3. un client avec plusieurs comptes consolides;
4. une operation fractionnee detectee;
5. une trace d'audit et un rapport exportable;
6. une promesse offline credible.

