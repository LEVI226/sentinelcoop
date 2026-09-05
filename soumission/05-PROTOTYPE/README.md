# SentinelleCoop — prototype

Filtrage LBC/FT/FP hors-ligne pour les coopératives financières.
Thématique 01 — Hackathon CIF / DigiCoop-WA+.

Prototype de la brique décisive : le moteur de correspondance phonétique
ouest-africaine, mesuré face à un Soundex de référence sur la **liste
consolidée réelle du Conseil de sécurité des Nations unies**.

## Prérequis

Python 3.11+. **Aucune dépendance externe** — c'est une contrainte de
conception, pas un hasard : la solution doit s'installer sur un poste de
guichet modeste, sans accès à un dépôt de paquets.

## Mise en route

```bash
# 1. Récupérer le référentiel ONU (une seule fois ; ~2 Mo)
curl -sL -o data/un_consolidated.xml \
     https://scsanctions.un.org/resources/xml/en/consolidated.xml

# 2. Vérifier l'ingestion
python -m sentinellecoop.ingest

# 3. Mesure comparative WAPE vs Soundex
python -m sentinellecoop.benchmark

# 4. Filtrer un client (débranchez le réseau : cela fonctionne toujours)
python -m sentinellecoop.screen "Amine Mohammed Oul Haq Sam Kan"
python -m sentinellecoop.screen "Salifou Ouedraogo"
```

## Résultats mesurés

Référentiel : 1 011 entrées ONU (736 personnes, 275 entités, 2 767 alias),
liste générée le 2026-08-18. Jeu de test : 99 couples de variantes
ouest-africaines attestées, 7 catégories. Bruit : 4 000 couples de noms sans
rapport tirés du référentiel.

| Méthode | Rappel | Bruit |
|---|---|---|
| Soundex strict (moteur classique) | 67,7 % | 0,0 % |
| Soundex souple | 70,7 % | 6,2 % |
| WAPE — code identique | 78,8 % | 0,0 % |
| **WAPE + similarité ≥ 0,80** (informatif) | **99,0 %** | 0,5 % |
| **WAPE + similarité ≥ 0,90** (bloquant) | **94,9 %** | 0,1 % |

Rappel par catégorie de variation :

| Catégorie | n | Soundex strict | WAPE ≥ 0,80 |
|---|---|---|---|
| palatalisation (Diallo / Jallo) | 12 | **8 %** | **100 %** |
| honorifique (El Hadj / Alhaji) | 7 | 57 % | 100 % |
| translittération (Ouédraogo / Wedraogo) | 30 | 70 % | 100 % |
| wolof (Ndiaye / Njaye) | 10 | 70 % | 90 % |
| sifflante (Cissé / Sisse) | 7 | 71 % | 100 % |
| arabe (Mohamed / Muhammad) | 28 | 86 % | 100 % |
| inversion nom/prénom | 5 | 100 % | 100 % |

La catégorie *palatalisation* est le résultat le plus net : Soundex détecte
8 % des couples Diallo / Jallo / Djallo, le moteur adapté 100 %. C'est la
séquence à montrer en démonstration.

Filtrage bout-en-bout : **520 ms** pour 1 011 entrées et 3 778 libellés, sur
un poste standard, hors ligne.

Sortie complète archivée dans `data/benchmark_resultats.txt`.

## Architecture

| Fichier | Rôle |
|---|---|
| `sentinellecoop/phonetics.py` | Encodage WAPE, Soundex témoin, Jaro-Winkler, Damerau-Levenshtein |
| `sentinellecoop/ingest.py` | Parsing du référentiel ONU vers un modèle normalisé |
| `sentinellecoop/matcher.py` | Alignement de jetons, pondération par rareté, double seuil |
| `sentinellecoop/benchmark.py` | Protocole de mesure rappel / bruit / marge |
| `sentinellecoop/screen.py` | Filtrage d'un client, décision art. 91, indicateur de fraîcheur |
| `data/variantes_noms_ao.csv` | Jeu de test — 99 couples de variantes |

### Deux décisions de conception non évidentes

**La moyenne harmonique des deux directions.** Un premier essai notait un
couple de noms par la meilleure des deux directions d'alignement. En
conditions réelles, le référentiel ONU contient des alias d'un seul jeton
(« Saleh », « Mohammad ») : la mesure unidirectionnelle leur accordait un
score parfait dès qu'un jeton voisin figurait dans le nom du client, et
« Salifou Ouédraogo » déclenchait dix alertes. Exiger un recouvrement
mutuel a ramené le bruit de 1,8 % à 0,5 % pour 4 points de rappel au seuil
bloquant. Ce défaut n'apparaît pas sur un jeu de test synthétique — seul le
passage sur données réelles l'a révélé.

**L'encodeur ne cherche pas l'égalité stricte.** Rendre `Muhammad` et
`Mahamadou` identiques exigerait des règles si destructrices qu'elles
confondraient des noms distincts. Le WAPE les *rapproche*, la distance de
chaînes tranche. C'est ce qui explique l'écart entre « code identique »
(78,8 %) et « code + similarité » (99,0 %) dans le tableau ci-dessus.

## Limites assumées

- Le jeu de 99 variantes est **construit à la main** à partir de règles de
  translittération connues, non collecté sur un portefeuille réel. Il mesure
  la couverture des règles, pas leur représentativité statistique. Le valider
  sur un échantillon anonymisé d'une coopérative membre est la première chose
  à faire.
- L'échantillon de bruit provient de la liste ONU, internationalement
  diverse, et non d'un portefeuille ouest-africain où les patronymes se
  répètent beaucoup. Le taux de faux positifs réel sera **supérieur** à
  0,5 %. C'est précisément ce que la pondération par rareté vise à contenir,
  et cela reste à mesurer.
- `Gueye / Gaye` n'est pas détecté (score 0,333). L'alternance `ue`/`a` du
  wolof n'est pas couverte par les règles actuelles.
- Le filtrage parcourt tout le référentiel. Un index de blocage sur le
  squelette consonantique (déjà présent dans `phonetics.squelette`) est la
  prochaine optimisation.
- Modules non encore implémentés : synchronisation différentielle (M1),
  profilage et consolidation multi-comptes (M3), surveillance comportementale
  (M4), production des actes de conformité (M5).
