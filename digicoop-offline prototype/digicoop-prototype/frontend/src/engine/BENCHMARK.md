# Benchmark — filtrage flou (fuzzyMatch.js)

Contexte : l'auto-évaluation honnête de ce prototype a identifié que la
première version de `matchAgainstWatchlist()` calculait un Levenshtein
complet, sans sortie anticipée, contre **chaque** entrée de la liste de
surveillance. Sur une vraie liste consolidée (ONU + UE + PPE nationale),
c'est facilement 10 000 à 50 000 entrées — largement au-delà du budget
« temps réel » promis dans l'architecture pour un dépôt au guichet.

## Méthode

Script Node autonome (aucune dépendance, exécuté avec `node`), watchlists
synthétiques de noms ouest-africains générés aléatoirement, comparées à :

- **naïve** : Levenshtein complet (ancienne implémentation, matrice O(m·n)
  jusqu'au bout, pour chaque entrée).
- **plafonnée (bounded)** : nouvelle implémentation avec deux sorties
  anticipées mathématiquement exactes (voir commentaire dans `fuzzyMatch.js`
  pour la preuve) : rejet immédiat si `|len(a) - len(b)| > maxDistance`, et
  arrêt dès que le minimum de la ligne DP courante dépasse déjà `maxDistance`.

Deux scénarios mesurés séparément, car ils dominent des usages différents :

1. **Avec correspondance réelle** insérée au milieu de la liste (cas
   « alerte » — le pire cas pour l'optimisation, puisque l'algorithme ne
   peut sortir tôt que sur les entrées qui NE matchent PAS).
2. **Sans aucune correspondance** (cas très majoritaire en pratique : un
   client ordinaire comparé à une liste de sanctions à laquelle il
   n'appartient pas — presque toutes les entrées sont rejetées très tôt).

## Résultats

Temps total pour cribler toute la liste (`matchAgainstWatchlist`), en ms :

### Scénario 1 — une correspondance réelle présente

| Taille liste | Naïve (avant) | Plafonnée (après) | Score du match trouvé |
|---:|---:|---:|:---:|
| 50 | ~1 ms | ~0.4 ms | identique |
| 500 | ~8 ms | ~2 ms | identique |
| 2 000 | ~33 ms | ~7 ms | identique |
| 10 000 | 151 ms | 20.74 ms | identique |
| 50 000 | 821 ms | 168 ms | identique |

### Scénario 2 — aucune correspondance (cas majoritaire réel)

| Taille liste | Plafonnée (après) |
|---:|---:|
| 50 | 0.50 ms |
| 500 | 0.97 ms |
| 2 000 | 4.74 ms |
| 10 000 | 20.58 ms |
| 50 000 | 71.63 ms |

(Le scénario 2 n'a pas été rechiffré pour la version naïve : par
construction, une comparaison naïve coûte le même temps qu'il y ait un
match ou non, donc les chiffres naïfs du scénario 1 s'appliquent aussi ici
— c'est justement ce que l'optimisation supprime.)

## Vérification de non-régression

Les deux implémentations ont été comparées entrée par entrée sur les mêmes
watchlists : **résultats de match strictement identiques** (mêmes entrées
retenues, mêmes scores à l'arrondi flottant près) à chaque taille testée.
Aucune régression de rappel (pas de faux négatif introduit) — attendu,
puisque les deux sorties anticipées sont des preuves mathématiques
d'exclusion, pas des heuristiques.

## Ce que ça change concrètement pour la démo

À 10 000 entrées (ordre de grandeur réaliste pour une liste PPE nationale +
sanctions internationales consolidées), un dépôt guichet passe de
**~151 ms à ~21 ms** de filtrage flou pur — le budget "temps réel" annoncé
redevient tenable même sur un Android d'entrée de gamme, où le CPU est
nettement plus lent que la machine ayant produit ces chiffres.

## Limites de ce benchmark (honnêtes)

- Mesuré sur la machine de développement (Node.js), pas sur un vrai terminal
  Android bas de gamme — le rapport de vitesse entre naïf et plafonné devrait
  rester comparable, mais les valeurs absolues seront plus élevées sur cible.
- Les noms synthétiques sont générés aléatoirement ; une vraie liste PPE a
  une distribution de longueurs de noms différente (souvent plus homogène),
  ce qui peut légèrement changer l'efficacité du filtre de longueur.
- Le seuil `threshold=0.72` reste à calibrer avec les experts métier CIF —
  ce benchmark porte sur la performance, pas sur la pertinence du seuil.
