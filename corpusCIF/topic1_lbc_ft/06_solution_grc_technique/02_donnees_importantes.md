# Données importantes pour Topic 1

## Données client

- Identifiant client non nominatif.
- Nom fictif, prénoms fictifs, alias, variantes orthographiques.
- Date et lieu de naissance fictifs.
- Pays de résidence, nationalité, zone d'activité.
- Type de client: habituel, occasionnel, personne physique, personne morale.
- Activité économique déclarée.
- Statut PPE simulé.
- Niveau de risque KYC calculé.

## Données compte

- Identifiant compte.
- Type de compte.
- Solde par compte.
- Solde global multi-comptes par client.
- Date d'ouverture.
- Statut du compte.
- Agence ou caisse.

## Données transaction

- Identifiant opération.
- Date et heure.
- Montant.
- Sens: débit ou crédit.
- Canal: guichet, mobile, agent, virement, caisse.
- Motif ou libellé.
- Contrepartie.
- Pays ou zone de destination si applicable.
- Fréquence et cumul par période.

## Données de surveillance

- Liste de sanctions synthétique.
- Liste PPE synthétique.
- Alias et translittérations.
- Dates d'ajout, modification et retrait.
- Source de la liste.
- Niveau de criticité.
- Type de mesure: blocage, revue renforcée, information.

## Variables calculées

- Score de similarité entre nom client et liste.
- Score de risque client.
- Nombre d'opérations sur 7, 30 et 90 jours.
- Cumul des montants par client et par canal.
- Écart par rapport au comportement habituel.
- Indicateur de fractionnement.
- Indicateur d'opération inhabituelle.
- Niveau d'alerte: informatif ou bloquant.

## Scénarios de démo à simuler

- Faux positif sur homonymie: même nom, date de naissance différente.
- PPE détectée à l'ouverture du compte.
- Client avec plusieurs comptes et solde global élevé.
- Fractionnement de dépôts sous un seuil.
- Transaction vers une contrepartie proche d'un nom sanctionné.
- Mise à jour de liste en mode connecté, puis filtrage hors ligne.
- Revue manuelle d'une alerte et traçabilité de la décision.

## Données à éviter

- Fichier client réel.
- Nom réel de client.
- Pièce d'identité réelle.
- Historique bancaire réel.
- Donnée nominative copiée depuis un système existant.

La démo doit assumer le synthétique. Le jury valorise la clarté des hypothèses, pas la possession de données réelles.
