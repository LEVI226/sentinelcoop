# Liste des sanctions ONU — référence (filtrage CIF)

Source officielle (Hackathon CIF · DigiCoop-WA+ 2026) :
- Liste consolidée ONU : `https://scsanctions.un.org/consolidated/`
- Export XML : `https://scsanctions.un.org/resources/xml/en/consolidated.xml`

## Principe du filtrage

Les règles Wazuh `100400`–`100409` (fichier `0501-regles-cif-uemoa.xml`) déclenchent sur les
**résultats de filtrage** produits par le moteur métier (champs `event_type` + `result`) :

| Champ `event_type` | `result` | Règle | Interprétation |
|---|---|---|---|
| `filtrage_sanctions` | `MATCH` | 100400 (12) | Personne/entité sanctionnée ONU identifiée |
| `virement/transfert/ordre_paiement` | `REJECTED`/`SUSPENDED` + `sanctioned=yes` | 100401 (14) | Transaction vers entité sanctionnée, bloquée (Dir. 02/2015/CM/UEMOA) |
| `filtrage_personnes` | `PEP_HIT` | 100402 (10) | Personne politiquement exposée |
| `filtrage_sanctions` | `POSSIBLE_MATCH`/`FUZZY`/`AMBIGUOUS` | 100403 (8) | Correspondance partielle → examen manuel CENTIF |
| `declaration_threshold` | `EXCEEDED` | 100404 (6) | Seuil déclaratif LBC/FT dépassé (loi uniforme 31/03/2023) |
| `transfert/virement` | `REVIEWED`/`SUSPENDED` + `risk_country=yes` | 100405 (10) | Destination pays sensible / embargo |
| `desactivation_filtrage` / `bypass_filtrage` | — | 100406 (13) | Contournement du dispositif CIF |
| `liste_sanctions_update` | `OK` | 100407 (5) | Mise à jour de la liste ONU réussie |
| `sfd_operation` | `REVIEWED` (montant ≥ 10M) | 100408 (9) | Opération SFD hors seuil prudentiel BCEAO |
| `liste_sanctions_update` | `FAILED` | 100409 (7) | Échec de mise à jour → filtrage potentiellement incomplet |

## Obtenir la liste et générer l'échantillon de référence

```bash
# Télécharger la liste consolidée (ONU) :
curl -s https://scsanctions.un.org/resources/xml/en/consolidated.xml -o consolidated.xml
# Extraire les noms (ex. avec xmlstarlet ou python) : balises FIRST_NAME/LAST_NAME/NAME.
# Construire la watchlist du moteur de filtrage (comparaison exacte + fuzzy).
```

> Échantillon démonstratif utilisé en test (`filtrage_sanctions` → `MATCH`) : `ABDOU YAYA`.
> Les noms réels doivent être extraits du XML consolidé ci-dessus ; cette liste n'est PAS exhaustive.