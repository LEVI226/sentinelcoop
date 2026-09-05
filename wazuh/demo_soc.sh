#!/bin/bash
# Demo SOC: securite SI + piste d'audit + regles de conformite (regles 100410-100428)
# Emission UDP/514 vers le manager Wazuh (fichier 0502-regles-securite-conformite-audit.xml)
set -e
exec 3<>/dev/udp/127.0.0.1/514
printf '%s\n' '{"event_type":"auth_failure","user":"tsc","src_ip":"10.0.0.9","result":"FAILED"}' >&3                       # 100410
printf '%s\n' '{"event_type":"privilege_escalation","user":"op_backoffice_7","target":"sudo_root","result":"GRANTED"}' >&3   # 100411
printf '%s\n' '{"event_type":"security_config_change","component":"moteur.js","config":"SEUIL_BLOQUANT","user":"op_admin","result":"DISABLED"}' >&3 # 100412
printf '%s\n' '{"event_type":"degraded_mode","component":"guichet","result":"ACTIVATED"}' >&3                                  # 100413
printf '%s\n' '{"event_type":"referentiel_fraicheur","source":"scsanctions.un.org","age_days":"12","result":"PERIME"}' >&3     # 100414
printf '%s\n' '{"event_type":"export_donnees","user":"op_exploitant","scope":"clients","volume":"153000"}' >&3               # 100415
printf '%s\n' '{"event_type":"service_down","service":"moteur_filtrage","result":"DOWN"}' >&3                                 # 100416
printf '%s\n' '{"event_type":"action_levage","user":"op_saisie","operation":"TRX-77891","result":"UNHABILITATED"}' >&3        # 100417
printf '%s\n' '{"event_type":"audit_tamper","record":"journal.jsonl","user":"root","result":"REWRITE"}' >&3                   # 100418
printf '%s\n' '{"event_type":"rapport_confidentiel","user":"co_rco","reference":"CEN-2026-07","result":"GENERATED"}' >&3      # 100419
printf '%s\n' '{"event_type":"ppe_evaluation","subject":"ONOMO Ibrahima","due_date":"2026-08-31","result":"LATE"}' >&3         # 100420
printf '%s\n' '{"event_type":"declaration_centif","transaction":"TRX-77891","delai_hours":"30","result":"MISSING"}' >&3       # 100421
printf '%s\n' '{"event_type":"consolidation_multi_compte","customer_id":"C-1029","cumul_7j":"1850000","result":"ALERT"}' >&3  # 100422
printf '%s\n' '{"event_type":"compte_rebond","customer_id":"C-3091","rebond_delai":"0h15","result":"BLOQUANT"}' >&3           # 100423
printf '%s\n' '{"event_type":"activation_dispersion","customer_id":"C-1029","beneficiaires":"3","fenetre":"6","result":"BLOQUANT"}' >&3 # 100424
printf '%s\n' '{"event_type":"fractionnement","customer_id":"C-1029","beneficiaires":"4","fenetre_jours":"10","result":"INFORMATIF"}' >&3 # 100425
printf '%s\n' '{"event_type":"operation_obnl","customer_id":"OBNL-X1","objet":"service","origine":"SN","destination":"SY","risk":"FT"}' >&3 # 100426
printf '%s\n' '{"event_type":"mobile_money","customer_id":"MM-7712","typology":"MULTI_COMPTE","result":"OBSERVED"}' >&3       # 100427
printf '%s\n' '{"event_type":"sync_differentielle","source":"scsanctions.un.org","signature":"BAD","result":"FAILED"}' >&3     # 100428
exec 3>&-
echo "19 evenements SOC envoyes (regles 100410-100428)."
echo "Verifier: python3 query_alerts.py 1004  (ou requete dediee)"