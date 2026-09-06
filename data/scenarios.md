# Dataset synthétique — filtrage, LBC, FT

**Toutes les données de ce fichier et des CSV associés (`clients.csv`, `comptes.csv`,
`transactions.csv`, `ppe_internes.csv`, `sanctions_demo.csv`) sont fictives**, construites pour
la démonstration du hackathon. Seul `data/un_consolidated.xml` (liste ONU) est une donnée réelle
et publique.

**Ce dataset reprend les 3 clients déjà codés en dur dans `demo/app.js`** (Diallo Mamadou, Awa
Sawadogo, Ouedraogo Salif), avec leurs mêmes identifiants, comptes et soldes — aucun client
supplémentaire n'a été inventé. Ce qui est ajouté ici, c'est l'horodatage des opérations
(`demo/app.js` ne stocke qu'une liste de montants sans dates) et deux typologies FT qui
n'existaient pas côté démo (celle-ci ne distingue que « Fractionnement » et « Compte rebond »,
sans séparer LBC et FT).

## Fichiers

| Fichier | Contenu |
|---|---|
| `clients.csv` | Les 3 clients de `demo/app.js`, avec type, PPE, agence |
| `comptes.csv` | Les 6 comptes déjà listés dans `demo/app.js`, mêmes soldes |
| `transactions.csv` | Les mêmes montants que `demo/app.js` (`client.transactions`) pour le filtrage et le rebond, plus les opérations FT ajoutées, toutes horodatées |
| `ppe_internes.csv` | Référentiel PPE interne — `PPE-BF-044` correspond à Ouedraogo Salif, déjà présent dans `watchlist` de `demo/app.js` |
| `sanctions_demo.csv` | Reprise exacte des 2 entrées de sanctions de `watchlist` (`ONU-DEM-017`, `ONU-DEM-061`) |
| `variantes_noms_ao.csv` *(existant)* | 99 paires nom/variante, jeu de test M2 utilisé par `benchmark.py` |
| `un_consolidated.xml` *(existant)* | Liste consolidée ONU réelle, 1011 entrées |

## Seuils utilisés

- **Cumul à 7 jours et seuil de fractionnement** : repris tels quels de `demo/app.js`
  (`analyzeClient` : `sevenDayTotal >= 1 500 000` et `amount < 500 000` pour compter comme
  fractionnement) — pas de nouveaux chiffres inventés pour cette partie.
- **Fenêtre de rebond, activation-dispersion, collecte fractionnée** : `demo/app.js` n'a pas
  d'équivalent horodaté (son critère de rebond est un raccourci : « un montant ≥ 750 000 et plus
  d'un compte », sans notion de délai) — ces seuils sont propres à `verdicts.py` et documentés
  dans son en-tête, à recalibrer sur un portefeuille réel comme le reste du prototype.
- **Seuil informatif de filtrage (M2)** : `matcher.SEUIL_INFORMATIF`, relevé de 0.80 à 0.88 le 5
  septembre 2026 après mesure (voir section suivante et l'en-tête de `matcher.py`).

## Verdicts attendus, par client

| Client | Comptes | Scénario | Verdicts attendus |
|---|---|---|---|
| **C-1029 — Diallo Mamadou** | 001-771 (860 000), 014-219 (410 000), 031-554 (230 000) | Nom déjà sanctionné (`ONU-DEM-017`) ; 4 dépôts de 430 000 à 480 000 FCFA sur le compte 001-771 en 4 jours (cumul 1 845 000, comme dans `demo/app.js`) ; 4 transferts de ~80-90 000 FCFA vers 4 bénéficiaires distincts sur le compte 014-219 (collecte FT) ; réception de 400 000 FCFA suivie en moins de 3h d'une dispersion de 425 000 FCFA vers 4 comptes sur le compte 031-554 (activation-dispersion FT) | **FILTRAGE bloquant**, **LBC informatif** (fractionnement + consolidation des 3 comptes = 1 500 000 FCFA, aucun compte seul au-dessus du seuil), **FT informatif** (collecte), **FT bloquant** (dispersion) |
| **C-2214 — Awa Sawadogo** | 008-194 (175 000) | 3 opérations modestes (25 000 / 14 000 / 35 000 FCFA), comme dans `demo/app.js` — témoin neutre | **Aucune alerte** |
| **C-3091 — Ouedraogo Salif** | 002-087 (950 000), 019-441 (320 000) | PPE (`PPE-BF-044`, déjà dans `watchlist`) ; réception de 800 000 FCFA suivie 45 minutes plus tard d'un transfert de 780 000 FCFA vers son second compte (compte rebond, comme dans `demo/app.js` où ce même montant de 800 000 déclenchait déjà « Compte rebond ») | **PPE informatif**, **LBC bloquant** (compte rebond) |

Diallo Mamadou porte volontairement plusieurs typologies à la fois : plutôt que d'inventer un
4e ou 5e client pour chaque scénario manquant (LBC ou FT), les techniques supplémentaires sont
posées sur ses comptes existants. C'est le profil déjà signalé par le filtrage nominal — le
scénario illustre qu'un même acteur à risque peut déclencher plusieurs mécanismes de détection
indépendants, plutôt que de disperser artificiellement les cas sur des identités inventées.

## Pourquoi LBC et FT sont distingués

Signature comportementale, pas seulement étiquette : le **fractionnement** (compte 001-771) a une
origine à dissimuler — 4 dépôts de montant élevé (430-480 000 FCFA), fractionnés uniquement pour
rester sous le seuil unitaire. La **collecte FT** (compte 014-219) est l'inverse : des montants
unitaires bien plus modestes (78-92 000 FCFA), vers des bénéficiaires distincts, sans mouvement
entrant qui les expliquerait. L'**activation-dispersion** (compte 031-554) combine réception
ponctuelle et redistribution rapide à plusieurs destinataires — le schéma que l'ENR BC/FT
(`data/enr_bcft.txt`) qualifie de risque émergent lié aux petits montants répétés.

## Résultat de la première exécution connectée au moteur (`verifier_dataset.py`)

**Première mesure (seuil informatif à 0.80, dataset à 10 clients inventés) :** 3/10 clients
conformes. Les 6 détections M3/M4/PPE ajoutées étaient exactes à 100 % ; le filtrage nominal (M2)
déclenchait une alerte informative en trop sur la plupart des témoins.

**Cause identifiée :** `benchmark.py` mesure le bruit sur des paires *un nom contre un seul autre
nom principal* (0,5 % de faux positifs annoncé au §3.1 de la note de présentation). Mais
`Index.filtrer()`, en usage réel, compare le nom saisi au nom **et à tous les alias** des 1011
entrées ONU — près de 3800 chaînes candidates par client filtré. Un taux mesuré par paire ne se
traduit pas au même taux une fois multiplié par ~3800 candidats.

**Correction appliquée :** `SEUIL_INFORMATIF` relevé de 0.80 à 0.88 dans `matcher.py` (voir son
en-tête pour le détail). Rappel sur `variantes_noms_ao.csv` inchangé à haute confiance (99,0 % ->
98,0 %, une seule variante perdue — `Sawadogo`/`Savadogo`, score 0,875, juste sous le nouveau
seuil), bruit mesuré par paire divisé par 5 (0,5 % -> 0,1 %).

**Mesure finale, sur le dataset reconstruit à partir des 3 clients de `demo/app.js`** (ce
fichier) : **3/3 clients conformes** à `python -m sentinellecoop.verifier_dataset`. Aucun faux
positif résiduel sur Awa Sawadogo (témoin) ; toutes les alertes attendues (filtrage, PPE,
fractionnement, collecte FT, dispersion FT, compte rebond) se déclenchent exactement.

**Point encore ouvert, à recalibrer sur un échantillon réel plutôt qu'à figer maintenant** : le
seuil 0.88 élimine le bruit sur ces 3 clients précis, mais rien ne garantit qu'un autre nom
ouest-africain arbitraire ne retombe pas au-dessus de ce seuil par coïncidence — la fenêtre entre
le 99e centile des paires sans rapport (0.780) et le 5e centile des vraies variantes (0.883) est
étroite. C'est exactement la limite que la note de présentation (§4.2) anticipait en demandant un
calibrage sur un échantillon anonymisé d'une coopérative membre.
