# DOSSIER DE CANDIDATURE

## Hackathon National d'Innovation CIF — Projet DigiCoop-WA+

| | |
|---|---|
| **Équipe** | SentinelleCoop |
| **Solution** | SentinelleCoop — filtrage LBC/FT/FP souverain et hors-ligne pour les coopératives financières |
| **Thématique** | **Thématique 01** — Filtrage des clients : conformité LBC/FT/FP en matière de système d'information |
| **Pays / Ville** | **Burkina Faso — Ouagadougou** (4-6 septembre 2026) |
| **Nombre de membres** | 4 |
| **Chef d'équipe** | OUEDRAOGO Yannick U. L. |
| **Contact unique** | ouedraogoyannick24@gmail.com — +226 70 85 99 88 |

---

## Correspondance avec la composition du dossier exigée par le TDR

Le TDR énumère sept pièces. Le tableau ci-dessous indique où chacune se trouve.

| Pièce exigée par le TDR | Emplacement dans ce dossier |
|---|---|
| Fiche de présentation de l'équipe — noms, prénoms, contacts, spécialités et rôles de chaque membre | `01-FICHE-PRESENTATION-EQUIPE` |
| Note de présentation de l'idée/solution (2 à 5 pages) — problème adressé, approche proposée, valeur ajoutée attendue | `02-NOTE-PRESENTATION-SOLUTION` |
| Indication de la thématique choisie | En-tête du présent sommaire, de la pièce 01 et de la pièce 02 |
| Mention du pays / ville de participation | En-tête du présent sommaire, de la pièce 01 et de la pièce 02 |
| CV ou profil synthétique de chaque membre de l'équipe | `03-PROFILS-SYNTHETIQUES-MEMBRES` |
| Copie d'une pièce d'identité du chef d'équipe | `04-PIECE-IDENTITE-CHEF-EQUIPE` |
| Tout autre document jugé pertinent (portfolio, prototype existant) | `05-PROTOTYPE` |

---

## Note sur la pièce 05 — le prototype

Le TDR admet comme document pertinent tout « prototype existant ». Le dossier en joint un, **fonctionnel et mesuré**.

Il ne s'agit pas d'une maquette : le moteur de correspondance phonétique ouest-africaine filtre la **liste consolidée réelle du Conseil de sécurité des Nations unies** — 1 011 entrées, 2 767 alias — et sa performance est comparée à un Soundex de référence sur un jeu de 99 couples de variantes.

| Méthode | Détection | Faux positifs |
|---|---|---|
| Soundex (moteur classique du marché) | 67,7 % | 0,0 % |
| Moteur adapté — seuil bloquant | **94,9 %** | 0,1 % |
| Moteur adapté — seuil informatif | **99,0 %** | 0,5 % |

L'écart le plus marqué porte sur la palatalisation — `Diallo` / `Jallo` / `Djallo` — où Soundex détecte 8 % des couples contre 100 % pour le moteur adapté. Le filtrage complet s'exécute en **520 millisecondes**, hors ligne, sur un poste standard.

Le protocole de mesure, les limites assumées du jeu de test et les instructions de reproduction figurent dans `05-PROTOTYPE/README.md`. La sortie brute du benchmark est jointe telle quelle dans `05-PROTOTYPE/data/benchmark_resultats.txt`.

Le prototype n'a **aucune dépendance externe** : Python 3.11+ suffit. C'est une contrainte de conception, pas un hasard — la solution doit pouvoir s'installer sur un poste de guichet sans accès à un dépôt de paquets.

---

## Contenu du dossier

```
00-SOMMAIRE
01-FICHE-PRESENTATION-EQUIPE
02-NOTE-PRESENTATION-SOLUTION
03-PROFILS-SYNTHETIQUES-MEMBRES
04-PIECE-IDENTITE-CHEF-EQUIPE/
05-PROTOTYPE/
   README                       mise en route, résultats mesurés, limites
   sentinellecoop/              moteur : phonétique, ingestion, correspondance, filtrage
   data/benchmark_resultats     sortie brute de la mesure comparative
   data/variantes_noms_ao       jeu de test — 99 couples, 7 catégories de variation
```

---

*Dossier déposé à digicoop-wa@cif-ao.org — clôture le 23 août 2026 à 23h59 GMT+0.*
