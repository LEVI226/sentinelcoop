> **Mise à jour du 6 septembre 2026 — préparation concours :** suivre [la recette du thème 1](docs/RECETTE_HACKATHON.md) et [le guide de maintenance sans IA](docs/MAINTENANCE_SANS_IA.md). Les commandes et résultats historiques sur la liste réelle ONU ci-dessous ne constituent pas une démonstration conforme à la règle des données synthétiques. Une similarité de nom ne confirme pas à elle seule une identité sanctionnée. La recette fonctionnelle reste à exécuter.

﻿# SentinelleCoop â€” prototype

Filtrage LBC/FT/FP hors-ligne pour les coopÃ©ratives financiÃ¨res.
ThÃ©matique 01 â€” Hackathon CIF / DigiCoop-WA+.

Prototype de la brique dÃ©cisive : le moteur de correspondance phonÃ©tique
ouest-africaine, mesurÃ© face Ã  un Soundex de rÃ©fÃ©rence sur la **liste
consolidÃ©e rÃ©elle du Conseil de sÃ©curitÃ© des Nations unies**.

## PrÃ©requis

Python 3.11+. **Aucune dÃ©pendance externe** â€” c'est une contrainte de
conception, pas un hasard : la solution doit s'installer sur un poste de
guichet modeste, sans accÃ¨s Ã  un dÃ©pÃ´t de paquets.

## Documentation de continuite

Pour reprendre le projet sans dependre d'une IA:

- `docs/REPRODUCTION_GUIDE.md`: etapes pour reconstruire le corpus Topic 1 et verifier les scripts.
- `CHANGELOG.md`: historique des evolutions du projet.
- `docs/PROMPTS_AND_DECISIONS.md`: prompts, decisions et fichiers produits.
- `corpusCIF/topic1_lbc_ft/README.md`: point d'entree du corpus nettoye LBC/FT/FP.
## Mise en route

```bash
# 1. RÃ©cupÃ©rer le rÃ©fÃ©rentiel ONU (une seule fois ; ~2 Mo)
curl -sL -o data/un_consolidated.xml \
     https://scsanctions.un.org/resources/xml/en/consolidated.xml

# 2. VÃ©rifier l'ingestion
python -m sentinellecoop.ingest

# 3. Mesure comparative WAPE vs Soundex
python -m sentinellecoop.benchmark

# 4. Filtrer un client (dÃ©branchez le rÃ©seau : cela fonctionne toujours)
python -m sentinellecoop.screen "Amine Mohammed Oul Haq Sam Kan"
python -m sentinellecoop.screen "Salifou Ouedraogo"
```

## RÃ©sultats mesurÃ©s

RÃ©fÃ©rentiel : 1 011 entrÃ©es ONU (736 personnes, 275 entitÃ©s, 2 767 alias),
liste gÃ©nÃ©rÃ©e le 2026-08-18. Jeu de test : 99 couples de variantes
ouest-africaines attestÃ©es, 7 catÃ©gories. Bruit : 4 000 couples de noms sans
rapport tirÃ©s du rÃ©fÃ©rentiel.

| MÃ©thode | Rappel | Bruit |
|---|---|---|
| Soundex strict (moteur classique) | 67,7 % | 0,0 % |
| Soundex souple | 70,7 % | 6,2 % |
| WAPE â€” code identique | 78,8 % | 0,0 % |
| **WAPE + similaritÃ© â‰¥ 0,80** (informatif) | **99,0 %** | 0,5 % |
| **WAPE + similaritÃ© â‰¥ 0,90** (bloquant) | **94,9 %** | 0,1 % |

Rappel par catÃ©gorie de variation :

| CatÃ©gorie | n | Soundex strict | WAPE â‰¥ 0,80 |
|---|---|---|---|
| palatalisation (Diallo / Jallo) | 12 | **8 %** | **100 %** |
| honorifique (El Hadj / Alhaji) | 7 | 57 % | 100 % |
| translittÃ©ration (OuÃ©draogo / Wedraogo) | 30 | 70 % | 100 % |
| wolof (Ndiaye / Njaye) | 10 | 70 % | 90 % |
| sifflante (CissÃ© / Sisse) | 7 | 71 % | 100 % |
| arabe (Mohamed / Muhammad) | 28 | 86 % | 100 % |
| inversion nom/prÃ©nom | 5 | 100 % | 100 % |

La catÃ©gorie *palatalisation* est le rÃ©sultat le plus net : Soundex dÃ©tecte
8 % des couples Diallo / Jallo / Djallo, le moteur adaptÃ© 100 %. C'est la
sÃ©quence Ã  montrer en dÃ©monstration.

Filtrage bout-en-bout : **520 ms** pour 1 011 entrÃ©es et 3 778 libellÃ©s, sur
un poste standard, hors ligne.

Sortie complÃ¨te archivÃ©e dans `data/benchmark_resultats.txt`.

## Architecture

| Fichier | RÃ´le |
|---|---|
| `sentinellecoop/phonetics.py` | Encodage WAPE, Soundex tÃ©moin, Jaro-Winkler, Damerau-Levenshtein |
| `sentinellecoop/ingest.py` | Parsing du rÃ©fÃ©rentiel ONU vers un modÃ¨le normalisÃ© |
| `sentinellecoop/matcher.py` | Alignement de jetons, pondÃ©ration par raretÃ©, double seuil |
| `sentinellecoop/benchmark.py` | Protocole de mesure rappel / bruit / marge |
| `sentinellecoop/screen.py` | Filtrage d'un client, dÃ©cision art. 91, indicateur de fraÃ®cheur |
| `data/variantes_noms_ao.csv` | Jeu de test â€” 99 couples de variantes |

### Deux dÃ©cisions de conception non Ã©videntes

**La moyenne harmonique des deux directions.** Un premier essai notait un
couple de noms par la meilleure des deux directions d'alignement. En
conditions rÃ©elles, le rÃ©fÃ©rentiel ONU contient des alias d'un seul jeton
(Â« Saleh Â», Â« Mohammad Â») : la mesure unidirectionnelle leur accordait un
score parfait dÃ¨s qu'un jeton voisin figurait dans le nom du client, et
Â« Salifou OuÃ©draogo Â» dÃ©clenchait dix alertes. Exiger un recouvrement
mutuel a ramenÃ© le bruit de 1,8 % Ã  0,5 % pour 4 points de rappel au seuil
bloquant. Ce dÃ©faut n'apparaÃ®t pas sur un jeu de test synthÃ©tique â€” seul le
passage sur donnÃ©es rÃ©elles l'a rÃ©vÃ©lÃ©.

**L'encodeur ne cherche pas l'Ã©galitÃ© stricte.** Rendre `Muhammad` et
`Mahamadou` identiques exigerait des rÃ¨gles si destructrices qu'elles
confondraient des noms distincts. Le WAPE les *rapproche*, la distance de
chaÃ®nes tranche. C'est ce qui explique l'Ã©cart entre Â« code identique Â»
(78,8 %) et Â« code + similaritÃ© Â» (99,0 %) dans le tableau ci-dessus.

## Limites assumÃ©es

- Le jeu de 99 variantes est **construit Ã  la main** Ã  partir de rÃ¨gles de
  translittÃ©ration connues, non collectÃ© sur un portefeuille rÃ©el. Il mesure
  la couverture des rÃ¨gles, pas leur reprÃ©sentativitÃ© statistique. Le valider
  sur un Ã©chantillon anonymisÃ© d'une coopÃ©rative membre est la premiÃ¨re chose
  Ã  faire.
- L'Ã©chantillon de bruit provient de la liste ONU, internationalement
  diverse, et non d'un portefeuille ouest-africain oÃ¹ les patronymes se
  rÃ©pÃ¨tent beaucoup. Le taux de faux positifs rÃ©el sera **supÃ©rieur** Ã 
  0,5 %. C'est prÃ©cisÃ©ment ce que la pondÃ©ration par raretÃ© vise Ã  contenir,
  et cela reste Ã  mesurer.
- `Gueye / Gaye` n'est pas dÃ©tectÃ© (score 0,333). L'alternance `ue`/`a` du
  wolof n'est pas couverte par les rÃ¨gles actuelles.
- Le filtrage parcourt tout le rÃ©fÃ©rentiel. Un index de blocage sur le
  squelette consonantique (dÃ©jÃ  prÃ©sent dans `phonetics.squelette`) est la
  prochaine optimisation.
- Modules non encore implÃ©mentÃ©s : synchronisation diffÃ©rentielle (M1),
  profilage et consolidation multi-comptes (M3), surveillance comportementale
  (M4), production des actes de conformitÃ© (M5).

