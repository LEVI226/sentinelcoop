# Notebooks — modèle de détection

## `modele_sentinellecoop.ipynb`

Cycle de vie complet du modèle : problème métier → données → EDA → construction du jeu →
entraînement → évaluation → décision de déploiement → intégration edge → surveillance.

### Résultat principal, en une phrase

**Le seuil de similarité 0.88 déjà en production n'a pas été amélioré par un modèle appris —
il a été validé.** Le notebook rapporte ce résultat négatif au lieu de le contourner.

| | coût moyen | faux positifs | faux négatifs | rappel |
|---|---|---|---|---|
| baseline 0.88 (production) | 24,0 ± 20,7 | **8,0 ± 6,8** | 0,8 ± 0,7 | 0,992 |
| régression logistique | 23,0 ± 15,0 | **19,0 ± 16,5** | 0,2 ± 0,4 | 0,998 |

Le modèle double les faux positifs pour éviter 0,6 faux négatif, ne gagne que sur 2 graines sur 5,
et l'écart moyen de coût (−1,0) vaut 5 % d'un seul écart-type. **Non promu.**

### Exécution

```powershell
pip install numpy pandas matplotlib
```

Puis ouvrir le fichier dans VS Code (extension Python) ou :

```powershell
pip install jupyter
jupyter notebook notebooks/modele_sentinellecoop.ipynb
```

Durée : environ 1 minute. Le notebook est **reproductible** — graines fixes, aucun `hash()` de
chaîne (qui est randomisé à chaque processus Python). Deux exécutions donnent les mêmes chiffres.

### Ce que le notebook contient

| Partie | Contenu |
|---|---|
| A | Modèle 1 — rapprochement de noms, **supervisé** sur les 99 paires attestées de `data/variantes_noms_ao.csv`, avec négatifs durs issus du vrai référentiel ONU |
| B | Modèle 2 — score de risque transactionnel, **non supervisé** (médiane + MAD), sans aucune étiquette inventée |
| C | Intégration edge : inférence en Python pur, latence mesurée, taille de l'artefact |

### Dépendances — le point important

| Moment | Bibliothèques |
|---|---|
| Ce notebook (portable, hors ligne, une fois) | numpy, pandas, matplotlib |
| **Le poste de guichet** | **aucune** — Python standard seul |

L'artefact produit fait ~1 Ko de JSON ; l'inférence est un produit scalaire, mesurée à **4 µs par
client**. numpy est un outil de construction, pas une dépendance d'exécution — la même relation
qu'entre un compilateur et le binaire qu'il produit. Le verdict « léger CONFORME » de
`wazuh/contraintes-modele-leger.md` (branche `feature/security_audit`) reste valide.

### Ce que le notebook ne fait pas

- Il ne remplace **aucun** composant existant. `matcher.py` et `verdicts.py` sont inchangés.
- Il n'annonce **aucune précision** pour le score transactionnel : il n'existe pas de vérité
  terrain, ce score priorise une file d'analyse, il ne qualifie pas une fraude.
- Il ne prend **aucune décision réglementaire** : chaque sortie porte
  `decision_operationnelle = NON_PRISE_PAR_LE_MOTEUR`.

### Pour aller plus loin

L'obstacle n'est pas l'algorithme, c'est le volume d'étiquettes : 99 paires, ~30 identités par
split. Pour conclure autrement il faudrait 1 000 à 5 000 paires étiquetées par un analyste
conformité sur un portefeuille réel anonymisé, plus les décisions historiques d'analystes
(confirmée / levée) — l'échantillon demandé au §4.2 de la note de présentation.
