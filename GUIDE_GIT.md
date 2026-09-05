# Guide Pratique Git & GitHub : Collaboration en Équipe

Bienvenue dans ce guide 101 ! Ce document a pour but de fournir à l'ensemble des membres de l'équipe, quel que soit leur niveau de maîtrise de Git, les bases nécessaires pour collaborer efficacement et sans heurts sur notre projet.

---

## Table des Matières
1. [Concepts Fondamentaux](#1-concepts-fondamentaux)
2. [Première Configuration](#2-première-configuration)
3. [Le Flux de Travail Standard (GitHub Flow)](#3-le-flux-de-travail-standard-github-flow)
4. [Gestion des Branches](#4-gestion-des-branches)
5. [Résolution de Problèmes Courants](#5-résolution-de-problèmes-courants)
6. [Bonnes Pratiques (À lire impérativement)](#6-bonnes-pratiques)

---

## 1. Concepts Fondamentaux

Avant de taper la moindre commande, il est essentiel de comprendre le vocabulaire de base :
- **Dépôt (Repository / Repo)** : Le dossier de votre projet qui est surveillé par Git.
- **Local vs Distant (Remote)** : Le code *local* est celui sur votre ordinateur. Le code *distant* (généralement nommé `origin`) est celui hébergé sur GitHub.
- **Branche (Branch)** : Une version parallèle du code. La branche principale s'appelle généralement `main` (ou `master`).
- **Commit** : Une "photographie" de votre code à un instant T. Un commit valide et sauvegarde vos modifications locales.
- **Push / Pull** : *Push* (pousser) envoie vos commits locaux vers GitHub. *Pull* (tirer) récupère les commits de GitHub vers votre ordinateur.
- **Pull Request (PR)** : Une demande officielle pour fusionner (intégrer) votre branche dans la branche principale.

---

## 2. Première Configuration

Si c'est votre premier jour sur le projet, voici les étapes à suivre pour configurer votre environnement.

### Cloner le dépôt
Récupérez le projet sur votre machine locale :
```bash
git clone https://github.com/LEVI226/sentinelcoop.git
cd sentinelcoop
```

### Configurer votre identité
Indiquez à Git qui vous êtes (ces informations apparaîtront dans l'historique du projet) :
```bash
git config --global user.name "Votre Prénom et Nom"
git config --global user.email "votre.email@exemple.com"
```

---

## 3. Le Flux de Travail Standard (GitHub Flow)

Voici la routine quotidienne stricte que **chaque membre de l'équipe** doit suivre pour développer une fonctionnalité ou corriger un bug.

### Étape 1 : Mettre à jour sa version locale
Avant de commencer à coder, assurez-vous d'avoir la dernière version de la branche principale :
```bash
git checkout main
git pull origin main
```

### Étape 2 : Créer une branche de travail
**Règle d'or : On ne code jamais directement sur la branche `main`.**
```bash
git checkout -b nom-de-ma-nouvelle-branche
```
*(Exemple : `git checkout -b feature/authentification`)*

### Étape 3 : Travailler et sauvegarder (Commit)
Une fois vos modifications terminées, ajoutez-les à l'historique Git :
```bash
# Ajoute toutes vos modifications
git add .

# Enregistre vos modifications avec un message clair
git commit -m "Ajout de la fonctionnalité d'authentification"
```

### Étape 4 : Envoyer son travail sur GitHub
Publiez votre branche locale vers le dépôt distant :
```bash
git push -u origin nom-de-ma-nouvelle-branche
```

### Étape 5 : Créer une Pull Request
1. Allez sur la page GitHub du projet.
2. Un bouton vert **"Compare & pull request"** devrait apparaître. Cliquez dessus.
3. Décrivez brièvement ce que vous avez fait et validez la création de la Pull Request.
4. Attendez qu'un autre membre de l'équipe relise votre code et le fusionne dans `main`.

---

## 4. Gestion des Branches

La maîtrise des branches est le cœur du travail d'équipe.

**Lister toutes les branches (locales et distantes) :**
```bash
git branch -a
```

**Changer de branche :**
```bash
git checkout nom-de-la-branche
```

**Récupérer le travail d'un collègue :**
Si un collègue a créé une branche et que vous voulez la tester sur votre machine :
```bash
git fetch
git checkout nom-de-la-branche-du-collegue
```

---

## 5. Résolution de Problèmes Courants

### Je me suis trompé de fichier dans mon `git add`
Pour retirer un fichier de la liste des modifications prêtes à être "commitées" :
```bash
git reset nom_du_fichier
```

### Git refuse mon `git push` car mon dépôt n'est pas à jour
Cela arrive si quelqu'un a modifié la même branche que vous sur GitHub.
```bash
git pull origin nom-de-ma-branche
# Résolvez les conflits éventuels, puis :
git push origin nom-de-ma-branche
```

### J'ai fait des modifications brouillonnes et je veux tout annuler
Pour ramener tous vos fichiers au dernier état "commit" (⚠️ **Attention, action irréversible**) :
```bash
git checkout .
```

---

## 6. Bonnes Pratiques

Pour garantir un historique propre et un projet stable, merci de respecter les règles suivantes :

1. **Messages de commit clairs** : Écrivez des messages explicites. 
   - *Mauvais :* `git commit -m "truc mis à jour"`
   - *Bon :* `git commit -m "Correction de la marge sur le bouton de soumission"`
2. **Des branches bien nommées** : Utilisez des préfixes pour indiquer la nature du travail.
   - `feature/xxx` pour une nouvelle fonctionnalité.
   - `bugfix/xxx` pour la correction d'un bug.
   - `docs/xxx` pour la documentation.
3. **Commits fréquents** : Faites des commits réguliers pour chaque petite étape logique de votre travail. N'attendez pas la fin de la semaine.
4. **Revue de code** : Ne validez jamais vos propres Pull Requests. Demandez toujours à un autre membre de l'équipe de relire votre code.

---
*Ce document est vivant : n'hésitez pas à proposer des modifications si vous découvrez de nouvelles astuces !*
