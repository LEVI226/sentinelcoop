#!/bin/bash
# ==============================================================================
# sync_github.sh — Audit automatique des branches de l'équipe SentinelleCoop
#
# Usage (relançable à volonté pour détecter les nouveautés des autres branches) :
#   bash sync_github.sh [--rapport]
#
# Rôle :
#   - Récupère (fetch) toutes les branches distantes du dépôt GitHub public.
#   - Compare chaque branche à feature/security_audit (socle SIEM wazuh).
#   - Détecte les NOUVEAUX commits et fichiers de chaque branche.
#   - Option --rapport : génère RAPPORT_SYNTHESE_BRANCHES.md.
#
# Pré-requis : git (pas de gh requis — dépôt public).
# Auteur    : PREDATOR (SOC UEMOA, 2026-09-05)
# ==============================================================================
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/LEVI226/sentinelcoop.git}"
LOCAL_DIR="${LOCAL_DIR:-$(cd "$(dirname "$0")" && pwd)}"
BRANCHE_CIBLE="feature/security_audit"
SORTIE_RAPPORT="$LOCAL_DIR/RAPPORT_SYNTHESE_BRANCHES.md"

# Condition : un clone miroir de travail existe-t-il ? sinon le créer.
# NB: clone --mirror génère un dépôt *bare* -> il n'y a pas de sous-dossier .git ;
#     on teste la présence de HEAD et config à la racine.
WORKDIR="$LOCAL_DIR/.sync-travail"

# Éviter le "dubious ownership" quand le clone est sur un montage /mnt/c (WSL)
git config --global --add safe.directory "$LOCAL_DIR" 2>/dev/null || true
git config --global --add safe.directory "$WORKDIR" 2>/dev/null || true

if [ ! -f "$WORKDIR/HEAD" ]; then
    if [ -d "$WORKDIR" ]; then
        echo ">> Dossier de travail résiduel détecté, purge…"
        rm -rf "$WORKDIR"
    fi
    echo ">> Clonage miroir de travail (fetch de toutes les branches)…"
    git clone --mirror "$REPO_URL" "$WORKDIR"
fi

cd "$WORKDIR" || exit 1

echo ">> Mise à jour des branches distantes (fetch --prune)…"
git fetch --prune origin "+refs/heads/*:refs/heads/*" 2>&1 | sed 's/^/   /'

# ---- 1. Comparaison : nouveautés de chaque branche vs cible ----
branches=$(git for-each-ref --format='%(refname:short)' refs/heads/ \
           | grep -v "^${BRANCHE_CIBLE}$")

echo ""
echo "=== NOUVEAUTÉS PAR BRANCHE (vs ${BRANCHE_CIBLE}) ==="

RAPPORT=""
for b in $branches; do
    # chemins des objets cibles
    if ! git rev-parse --verify "$BRANCHE_CIBLE" >/dev/null 2>&1; then
        echo "   [skip] branche cible absente localement"
        continue
    fi
    if ! git rev-parse --verify "$b" >/dev/null 2>&1; then
        continue
    fi
    head_cible=$(git rev-parse --short "$BRANCHE_CIBLE")
    head_b=$(git rev-parse --short "$b")
    sujet_b=$(git log -1 --format='%s' "$b")

    # fichiers ABSENTS de la cible (nouveautés à surveiller/potentiellement intégrer)
    nouveaux=$(git diff --name-status "$BRANCHE_CIBLE" "$b" 2>/dev/null \
               | awk '$1 ~ /^A/ {print $2}' | head -40)

    # composants remarquables d'intérêt SIEM présents sur la branche
    flags=""
    [ -n "$(git ls-tree -r --name-only "$b" guichet/ 2>/dev/null)" ] \
        && flags="$flags  + guichet/ (evenements poste : degrade/fraicheur/journal -> 100413/414/418)"
    [ -n "$(git ls-tree -r --name-only "$b" sentinellecoop/verdicts.py 2>/dev/null)" ] \
        && flags="$flags  + verdicts.py (M3/M4 : consolidation/rebond/dispersion/fractionnement -> 100422-100425)"
    [ -n "$(git ls-tree -r --name-only "$b" data/verdicts_demo.json 2>/dev/null)" ] \
        && flags="$flags  + data/verdicts_demo.json (verdicts precalculés exportables via feed_wazuh.py)"
    [ -n "$(git ls-tree -r --name-only "$b" corpusCIF/ 2>/dev/null)" ] \
        && flags="$flags  + corpusCIF/ (corpus reglementaire de conformité)"

    echo ""
    echo "--- $b ---"
    echo "   HEAD local : $head_b — $(echo "$sujet_b" | cut -c1-60)"
    echo "   HEAD cible : $head_cible"
    [ -n "$flags" ] && { echo "   Composants SIEM remarquables :"; echo "$flags" | sed 's/^/\n/'; }

    if [ -n "$nouveaux" ]; then
        echo "   Nouveaux fichiers (ajoutés vs cible) : $(echo "$nouveaux" | wc -l)"
        echo "$nouveaux" | sed 's/^/      + /'
    else
        echo "   Aucun nouveau fichier détecté."
    fi

    RAPPORT+="\n## $b (HEAD $head_b — $sujet_b)\n"
    [ -n "$flags" ] && RAPPORT+="\n**Composants SIEM remarquables :** $(echo "$flags" | tr -s ' ' | sed 's/^ *//')\n"
    if [ -n "$nouveaux" ]; then
        RAPPORT+="\nFichiers ajoutés par rapport à $BRANCHE_CIBLE :\n$(echo "$nouveaux" | sed 's/^/  - /')\n"
    else
        RAPPORT+="\nAucun nouveau fichier par rapport à la cible.\n"
    fi
done

# ---- 2. Relevé du dernier commit par branche (historique d'audit) ----
echo ""
echo "=== DERNIERS COMMITS PAR BRANCHE ==="
for b in $branches; do
    echo "  - $b : $(git log -1 --format='%h %s' "$b" | cut -c1-90)"
done

# ---- 3. Option --rapport : écrire le rapport de synthèse ----
RAPPORT_OPT="no"
for a in "$@"; do
    [ "$a" = "--rapport" ] && RAPPORT_OPT="yes"
done

if [ "$RAPPORT_OPT" = "yes" ]; then
    {
        echo "# RAPPORT DE SYNTHÈSE DES BRANCHES — SentinelleCoop"
        echo ""
        echo "Généré le : $(date '+%Y-%m-%d %H:%M:%S' )"
        echo "Branche de référence (socle SIEM Wazuh) : \`${BRANCHE_CIBLE}\`"
        echo ""
        echo "Synthèse de l'état de chaque branche et de ses nouveautés. Ce fichier est"
        echo "régénéré par \`bash sync_github.sh --rapport\`."
        echo -e "$RAPPORT"
    } > "$SORTIE_RAPPORT"
    echo ""
    echo ">> Rapport généré : $SORTIE_RAPPORT"
fi

echo ""
echo "Terminé. Node cible : $BRANCHE_CIBLE (HEAD $(git rev-parse --short "$BRANCHE_CIBLE"))"
echo "Pour relancer l'audit à tout moment : bash sync_github.sh --rapport"