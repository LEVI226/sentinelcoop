# Workflows opérations de caisse

## Création de compte

### Étapes

1. Saisie client personne physique ou morale.
2. Vérification des champs KYC obligatoires.
3. Contrôle validité CNIB ou pièce équivalente.
4. Filtrage sanctions, PPE et alias.
5. Attribution d'un score de risque.
6. Ouverture du compte si aucune alerte bloquante.
7. Journalisation de la décision.

### Alertes possibles

- Pièce expirée.
- Client proche d'un nom sanctionné.
- PPE détectée.
- Bénéficiaire effectif manquant pour personne morale.
- Client déjà présent dans une autre caisse.
- Zone de résidence ou activité économique à risque.

## Dépôt

### Données à saisir

- compte;
- montant;
- canal;
- motif;
- origine des fonds;
- déposant réel;
- justificatif si seuil dépassé;
- caisse et agent.

### Règles de contrôle

- montant supérieur au seuil de justification;
- cumul de dépôts sur période;
- fractionnement sous seuil;
- dépôt par tiers fréquent;
- incohérence avec activité déclarée;
- dépôt dans une caisse différente de la caisse habituelle;
- opération en zone rouge.

## Retrait

### Données à saisir

- compte;
- montant;
- bénéficiaire;
- motif;
- canal;
- pièce présentée;
- formulaire de retrait;
- signature ou validation.

### Règles de contrôle

- montant supérieur au comportement habituel;
- retrait après dépôt récent élevé;
- retrait dans une autre caisse;
- retrait répété sur courte période;
- retrait en zone à risque;
- CNIB expirée ou incohérente.

## Retrait par procuration

### Données à saisir

- client donneur d'ordre;
- mandataire;
- pièce du mandataire;
- mandat ou procuration;
- durée de validité;
- plafond autorisé;
- compte concerné;
- motif.

### Règles de contrôle

- procuration expirée;
- plafond dépassé;
- mandataire lié à plusieurs clients;
- mandataire proche d'une liste PPE/sanction;
- retrait par procuration répété;
- absence de justificatif;
- opération dans une zone rouge.

## Formulaire de retrait

Le formulaire doit alimenter le moteur de contrôle:

- identité du titulaire;
- identité du mandataire si applicable;
- montant;
- motif;
- référence de pièce;
- validité de pièce;
- signature;
- agent ayant traité;
- horodatage.

## Carnet bancaire ou carnet caisse

Le carnet peut servir à rapprocher:

- identité locale du client;
- numéro de compte;
- opérations papier;
- retraits au guichet;
- incohérences entre saisie digitale et support physique.

Pour le MVP, il suffit de simuler un champ `reference_carnet` et un scan fictif ou statut de vérification.

## Produits à couvrir

- épargne;
- compte courant ou compte de dépôt;
- crédit;
- tontine ou produit assimilé si utilisé localement;
- services digitaux ou mobile money si la caisse les propose;
- opérations de transfert si disponibles.

## Sortie attendue

Chaque opération doit produire soit:

- aucune alerte;
- une alerte informative;
- une alerte bloquante;
- une demande de justificatif;
- une revue conformité.
