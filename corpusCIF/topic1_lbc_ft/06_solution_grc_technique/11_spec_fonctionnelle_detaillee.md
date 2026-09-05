# Spécification fonctionnelle détaillée Topic 1

## Objectif fonctionnel

Fournir aux SFD du réseau CIF un outil léger pour détecter les risques LBC/FT/FP lors de l'entrée en relation et pendant les opérations courantes de caisse.

## Acteurs

- Client personne physique.
- Client personne morale.
- Mandataire.
- Agent de caisse.
- Chef de caisse.
- Responsable conformité caisse.
- Responsable conformité réseau.
- Auditeur.
- Administrateur.

## Objets métier

- Caisse.
- Client.
- Pièce d'identité.
- Bénéficiaire effectif.
- Compte.
- Produit.
- Opération.
- Procuration.
- Justificatif.
- Liste de surveillance.
- Alerte.
- Décision conformité.
- Journal d'audit.

## Exigences fonctionnelles

| Code | Exigence | Priorité |
| --- | --- | --- |
| F001 | Créer un client personne physique avec KYC minimal | Haute |
| F002 | Créer un client personne morale avec bénéficiaire effectif | Haute |
| F003 | Vérifier la validité de la CNIB ou pièce équivalente | Haute |
| F004 | Filtrer client contre sanctions et PPE | Haute |
| F005 | Gérer les homonymies et variantes de noms | Haute |
| F006 | Ouvrir un compte dans une caisse | Haute |
| F007 | Relier plusieurs comptes à un même client réseau | Haute |
| F008 | Saisir dépôt, retrait, virement ou retrait par procuration | Haute |
| F009 | Demander origine des fonds et justificatif selon seuil | Haute |
| F010 | Détecter cumul et fractionnement | Haute |
| F011 | Détecter opération inhabituelle selon profil | Moyenne |
| F012 | Paramétrer seuils par caisse et zone | Haute |
| F013 | Gérer alertes informatives et bloquantes | Haute |
| F014 | Traiter une alerte avec décision humaine | Haute |
| F015 | Journaliser toute action sensible | Haute |
| F016 | Importer ou mettre à jour listes sanctions/PPE | Haute |
| F017 | Fonctionner avec liste locale hors connexion | Haute |
| F018 | Masquer données selon rôle utilisateur | Haute |
| F019 | Exporter un rapport d'alertes | Moyenne |
| F020 | Produire indicateurs conformité | Moyenne |

## Règles de décision

- Une correspondance sanction forte bloque l'opération.
- Une correspondance sanction moyenne ouvre une revue conformité.
- Une PPE ne bloque pas automatiquement, mais impose une vigilance renforcée.
- Une CNIB expirée bloque l'ouverture de compte et les retraits sensibles.
- Un seuil dépassé impose une justification de fonds.
- Une procuration expirée bloque le retrait.
- Une zone rouge abaisse les seuils et augmente le score de risque.
- Une liste obsolète déclenche une alerte administrateur.

## Données de démonstration minimales

- 2 caisses: Dori et Banfora.
- 8 clients personnes physiques.
- 3 personnes morales.
- 2 bénéficiaires effectifs.
- 12 comptes.
- 40 opérations.
- 4 mandats/procurations.
- 10 entrées sanctions/PPE synthétiques.
- 12 alertes générées.

## Écrans MVP

- Connexion et choix rôle.
- Tableau de bord caisse.
- Fiche client KYC.
- Création compte.
- Saisie opération.
- Résultat filtrage.
- File d'alertes.
- Détail alerte et décision.
- Paramétrage caisse.
- Journal d'audit.
