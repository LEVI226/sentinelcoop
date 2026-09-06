# Dataset synthétique Topic 1

Ce dataset sert à démontrer une solution LBC/FT/FP pour le réseau CIF.

Toutes les données sont fictives. Aucun client réel, aucune pièce réelle, aucune transaction réelle.

## Fichiers

- `caisses.csv`: caisses et paramètres locaux.
- `clients.csv`: clients physiques et moraux.
- `pieces_identite.csv`: pièces fictives et validité CNIB.
- `beneficiaires_effectifs.csv`: bénéficiaires effectifs des personnes morales.
- `comptes.csv`: comptes par caisse et client réseau.
- `mandats_procurations.csv`: procurations et mandataires.
- `listes_surveillance_synthetiques.csv`: entrées sanctions/PPE fictives.
- `operations.csv`: opérations de caisse.
- `alertes_attendues.csv`: alertes que le moteur doit retrouver.
- `roles_permissions.csv`: permissions par rôle.

## Ce que le dataset permet de tester

- Client avec comptes dans plusieurs caisses.
- Dori en zone rouge et Banfora en zone verte.
- Dépôts fractionnés.
- Retrait par procuration avec mandat expiré.
- CNIB expirée.
- Personne morale avec bénéficiaire effectif PPE.
- Matching de noms avec alias et translittérations.
- Alertes informatives et bloquantes.
- Visibilité différenciée selon rôle.

## Utilisation recommandée

1. Charger les CSV dans SQLite.
2. Afficher les caisses et leurs seuils.
3. Afficher les clients et comptes.
4. Exécuter le moteur de filtrage sur `clients.csv`.
5. Exécuter le moteur de règles sur `operations.csv`.
6. Comparer les alertes générées avec `alertes_attendues.csv`.

## Résolution d'identité réseau (NIP/CNIB)

`sentinellecoop/reseau.py` répond au besoin « combien de comptes un même client
détient-il à travers le réseau ? » sans se fier au `global_client_id` déjà
présent dans `clients.csv` — en production, cet identifiant réseau n'existe
pas encore, seule la caisse d'origine, le nom et la pièce d'identité
(`pieces_identite.csv`) sont disponibles.

Règle 1 : même numéro de pièce (CNIB/NIP/RCCM) -> même personne.
Règle 2 (secours, pièce absente) : même date de naissance ET similarité de
nom (moteur `matcher.similarite_nom`, déjà utilisé pour le filtrage
sanctions/PPE — un seul algorithme de rapprochement, pas deux à maintenir).

```powershell
python -m sentinellecoop.reseau
```

Vérifie automatiquement que le regroupement recalculé correspond au
`global_client_id` du dataset (0 écart attendu) et détecte le cas
KABORE AMADOU (comptes à Dori ET Banfora, solde consolidé 1 405 000 FCFA,
cf. `alertes_attendues.csv` ALT_003).

## Critère de réussite

Le MVP doit générer au moins les alertes présentes dans `alertes_attendues.csv`,
expliquer chaque alerte par une règle lisible, et retrouver sans écart les
identités réseau multi-caisses via `sentinellecoop/reseau.py`.
