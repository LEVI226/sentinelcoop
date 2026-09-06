# WORKFLOW — Back-end_filtrage (CIF Guard)

Méthode de travail et procédures techniques du projet, inspirée du référentiel
TECHNIUM (qui s'inspire lui-même du socle UEMOA/SOC).

Cible : maintenance **sans IA** et reproduction fiable des opérations.

---

## 1. Méthode de travail

### 1.1 Règle d'or

> Chaque demande donne lieu à une entrée `CHANGELOG.md` avant la clôture de session,
> et chaque prompt est archivé dans `PROMPTS.md`.

### 1.2 Structure d'une entrée de session

| Section | Contenu |
|---|---|
| **Contexte** | La demande utilisateur citée verbatim + le besoin réel |
| **Plan / état de départ** | Architecture, valeurs avant modification |
| **Étapes réalisées** | Suite numérotée des actions concrètes |
| **Incidents / pièges** | Ce qui a résisté, pourquoi, marche à suivre fiable |
| **Validation** | Preuves mesurables : commande → résultat |
| **Fichiers modifiés** | Liste exhaustive |
| **Prompts utilisés** | Demandes telles que posées |

### 1.3 Règles de rigueur

1. Sauvegarder avant opération sensible (reset DB, migrations destructrices).
2. Validation par preuve, pas par intention.
3. Secrets jamais dans le code source (toujours `.env`).
4. Ne jamais committer sans demande explicite.
5. Fichier source = référence ; volumes/miroirs = cibles de déploiement.

---

## 2. Procédures techniques

### 2.1 Démarrage / arrêt

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

### 2.2 Base de données (ordre canonique)

```powershell
alembic upgrade head          # appliquer les migrations
python -m app.scripts.seed    # données de démonstration
```

### 2.3 Clés & secrets

```powershell
python -m app.scripts.genkeys   # génère JWT_SECRET + ENCRYPTION_MASTER_KEY → .env
```

### 2.4 Smoke test

```powershell
python -c "import urllib.request,json; print(json.load(urllib.request.urlopen('http://localhost:8000/health')))"
```

### 2.5 Avant de relancer après modification

1. `python -m py_compile <fichier.py>` (syntaxe).
2. Redémarrer uvicorn.
3. Vérifier `/health` + appels API touchés.

---

## 3. Historique des sessions

Voir `CHANGELOG.md` (gabarit ci-dessus). Prompts archivés dans `PROMPTS.md`.

---

## 4. Index de documentation

| Document | Rôle |
|---|---|
| `README.md` | Installation, config, commandes, dépannage |
| `CHANGELOG.md` | Historique des évolutions |
| `WORKFLOW.md` | Méthodes de travail (ce document) |
| `PROMPTS.md` | Archive des demandes utilisateur |
| `docs/architecture.md` | Architecture technique |
| `docs/security.md` | Sécurité & chiffrement |
| `docs/api.md` | Référence API |
| `.env` | Secrets (jamais commité) |
