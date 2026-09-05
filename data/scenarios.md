# Dataset synthétique — filtrage, LBC, FT

**Toutes les données de ce fichier et des CSV associés (`clients.csv`, `comptes.csv`,
`transactions.csv`, `ppe_internes.csv`) sont fictives**, construites pour la démonstration du
hackathon. Aucun nom, montant ou identifiant ne correspond à une personne ou une opération
réelle. Seul `data/un_consolidated.xml` (liste ONU) est une donnée réelle et publique.

Ce fichier est la **clé de lecture** du dataset : pour chaque client, le comportement attendu du
moteur (déclenche / ne déclenche pas), le type d'alerte, et la base légale, en s'appuyant sur les
modules M1-M5 et le tableau de couverture de `soumission/02-NOTE-PRESENTATION-SOLUTION.md`.
Sert de jeu de test pour `feature/moteur-ia` (M3), `feature/offline-sync` (M1/PPE) et
`feature/securite-audit` (M5) — les mêmes identifiants doivent produire les mêmes verdicts,
quel que soit qui les implémente.

## Fichiers

| Fichier | Contenu | Volume |
|---|---|---|
| `clients.csv` | Identité, type (habituel/occasionnel), PPE, agence, scénario | 10 clients |
| `comptes.csv` | Comptes rattachés à un client, avec solde | 15 comptes |
| `transactions.csv` | Mouvements horodatés, avec contrepartie et canal | 37 transactions |
| `ppe_internes.csv` | Référentiel PPE interne, distinct des listes de sanctions | 3 entrées |
| `variantes_noms_ao.csv` *(existant)* | 99 paires nom/variante ouest-africaine | jeu de test M2, déjà utilisé par `benchmark.py` |
| `un_consolidated.xml` *(existant)* | Liste consolidée ONU réelle | 1011 entrées, utilisée par `ingest.py` |

## Seuils de démonstration

Ces seuils ne sont **pas réglementaires** — ils sont fixés pour que le dataset produise des
alertes claires en démo, et doivent être recalibrés avec une institution réelle (cf. `PLAN.md`,
`docs/PRD.md` — hors portée MVP démo) :

- **Seuil de cumul à 7 jours** : 500 000 FCFA. Franchi par accumulation → alerte fractionnement.
- **Fenêtre de rebond** : moins de 2 heures entre une réception et un transfert sortant de montant
  proche → alerte compte rebond.
- **Seuil de consolidation multi-comptes** : 500 000 FCFA de solde global, alors qu'aucun compte
  pris isolément ne le dépasse.

## Verdicts attendus, par client

| Client | Scénario | Type attendu | Déclenche | Base légale | Module |
|---|---|---|---|---|---|
| C-1001 DIALLO Mamadou | `filtrage_positif` | **Filtrage — bloquant** | Oui : le nom saisi rapproche de la variante `Djallo Mamadou` déjà connue (`ONU-DEM-017` dans `demo/app.js`) | Art. 20, 91 | M2 |
| C-1002 SAWADOGO Awa | `temoin_neutre` | Aucune alerte | Non : activité faible et cohérente, aucun rapprochement | — | témoin |
| C-1003 OUEDRAOGO Salif | `ppe_multi_comptes` | **PPE — informatif + solde consolidé** | Oui : présent dans `ppe_internes.csv` (`PPE-BF-044`) ; solde global des 3 comptes = 1 450 000 FCFA | Art. 29, 13 e) | M1 + M3 |
| C-1004 KONE Fatimata | `fractionnement_lbc` | **LBC — informatif (fractionnement)** | Oui : 4 dépôts de 160 000 à 190 000 FCFA en 5 jours, cumul 700 000 FCFA, aucun dépôt individuellement suspect | Art. 21 a), 23 | M3 |
| C-1005 TRAORE Boureima | `compte_rebond_lbc` | **LBC — bloquant (compte rebond)** | Oui : réception de 500 000 FCFA suivie 45 minutes plus tard d'un transfert sortant de 480 000 FCFA — signature de layering | Art. 13 f), 60 | M4 |
| C-1006 KABORE Alassane | `consolidation_multi_comptes_lbc` | **LBC — informatif (consolidation)** | Oui : 4 comptes de 130 000 FCFA répartis sur 4 agences, solde global 520 000 FCFA au-dessus du seuil alors qu'aucun compte seul ne le dépasse | Art. 13 e) | M3 |
| C-1007 ZONGO Ibrahim | `collecte_fractionnee_ft` | **FT — informatif (collecte fractionnée)** | Oui : 6 transferts sortants de ~30 000 FCFA sur 6 jours vers 6 bénéficiaires externes distincts, sans activité commerciale déclarée — schéma de collecte/redistribution, pas de layering classique LBC | Art. 21 a), 60 | M4 |
| C-1008 SANA Hamidou | `activation_dispersion_ft` | **FT — bloquant (activation puis dispersion)** | Oui : compte quasi dormant (solde 5 000 FCFA) qui reçoit 600 000 FCFA puis les disperse en moins de 2 heures vers 4 comptes externes distincts | Art. 60, 91 | M4 |
| C-1009 OUATTARA Salamata | `temoin_faux_positif_volume` | Aucune alerte malgré le volume | Non : grossiste avec rationale commerciale déclarée (`rationale_activite` dans `clients.csv`), mouvements réguliers et cohérents avec son activité — sert à mesurer le taux de faux positifs (cf. `benchmark.py`, §3.1 de la note) | — | témoin |
| C-1010 SAWADOGO Amidou | `temoin_similarite_nom` | Aucune alerte de filtrage | Non : proche phonétiquement de `SAWADOGO Awa` (C-1002) et de la racine `Ouédraogo`, mais ne correspond à aucune entrée de la liste ONU ni du référentiel PPE — contrôle de non-sur-déclenchement, complémentaire aux paires de `variantes_noms_ao.csv` | — | témoin M2 |

## Pourquoi LBC et FT sont distingués

La loi n° 046-2024/ALT traite la LBC et le FT comme deux infractions distinctes, et le TDR nomme
les deux dans l'intitulé de la Thématique 01. Le dataset les distingue par **signature
comportementale**, pas seulement par étiquette :

- **LBC (C-1004, C-1005, C-1006)** — l'argent a une origine à dissimuler : fractionnement d'un
  dépôt, transfert rapide pour brouiller la trace (layering), répartition sur plusieurs comptes
  pour rester sous les seuils. Montants relativement élevés, mouvement souvent unidirectionnel
  (entrée → sortie rapide, ou accumulation).
- **FT (C-1007, C-1008)** — la logique est inverse : collecter de petites sommes auprès de
  plusieurs sources ou les redistribuer à plusieurs destinataires, montants unitaires modestes
  précisément pour rester sous le radar, absence de rationale commerciale. C'est le schéma que
  l'ENR BC/FT (`data/enr_bcft.txt`) qualifie de risque émergent lié aux petits montants répétés.

Un moteur qui ne détecterait que les gros montants isolés manquerait le FT ; un moteur qui
alerterait sur tout mouvement fréquent noierait C-1009 sous les fausses alertes. Le dataset est
construit pour que les deux échecs soient visibles si le calibrage est mauvais.

## Utilisation

- **Test unitaire / benchmark M3-M4** : charger `clients.csv`, `comptes.csv`, `transactions.csv`
  et vérifier que chaque client produit le verdict de la colonne « Type attendu » ci-dessus —
  aucun de plus, aucun de moins (les témoins ne doivent produire aucune alerte).
- **Démo pitch** : les scénarios C-1001 (filtrage), C-1005 (LBC bloquant), C-1007 ou C-1008 (FT),
  C-1006 (consolidation) couvrent les 4 minutes du pitch sans redondance.
- Ce dataset ne remplace pas `variantes_noms_ao.csv` (99 paires, déjà utilisé par
  `benchmark.py` pour mesurer le moteur M2) : les deux sont complémentaires, l'un teste le nom,
  l'autre teste le comportement transactionnel.
