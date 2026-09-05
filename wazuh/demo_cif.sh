#!/bin/bash
# Demo CIF/LBC-FT : emission de logs de filtrage via UDP/514
# (regles 100400-100409 ~ liste des sanctions ONU, Directive 02/2015/CM/UEMOA)
set -e
echo "=== Envoi de logs CIF via UDP/514 (simulation moteur de filtrage LBC/FT) ==="
exec 3<>/dev/udp/127.0.0.1/514
printf '%s\n' '{"event_type":"filtrage_sanctions","mode":"ONU_consolidated","source":"scsanctions.un.org","subject":"ABDOU YAYA","result":"MATCH"}' >&3
printf '%s\n' '{"event_type":"virement","customer_id":"CI100091","beneficiary":"ORGANISATION ALPHA","amount":"500000","sanctioned":"yes","result":"REJECTED"}' >&3
printf '%s\n' '{"event_type":"filtrage_personnes","subject":"MAMADOU TOURE","result":"PEP_HIT","source":"GIABA"}' >&3
printf '%s\n' '{"event_type":"declaration_threshold","customer_id":"CI555001","amount":"11000000","result":"EXCEEDED"}' >&3
printf '%s\n' '{"event_type":"desactivation_filtrage","customer_id":"op_backoffice_7","src_ip":"10.0.0.5"}' >&3
printf '%s\n' '{"event_type":"liste_sanctions_update","source":"scsanctions.un.org","records":"3231","result":"FAILED"}' >&3
exec 3>&-
echo "6 logs CIF envoyes (regles 100400/100401/100402/100404/100406/100409)."
echo "Verifier ensuite avec: python3 query_alerts.py  (ou requete dediee 1004xx)"