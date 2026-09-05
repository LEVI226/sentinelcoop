#!/bin/bash
# AGENT-011 - THREAT INTELLIGENCE + FILTRAGE CIF/LBC-FT + SECURITE SI / AUDIT / CONFORMITE
mkdir -p /var/technium/logs /var/ossec/etc/lists
touch /var/technium/logs/app.log /var/technium/logs/error.log /var/technium/logs/requests.log

# Create malicious IP list (management file for Wazuh)
cat > /var/ossec/etc/lists/malicious-ips << 'EOF'
8.8.8.8
1.1.1.1
185.220.101.1
45.155.205.1
91.219.236.1
EOF

i=0
while true; do
  i=$((i+1))
  TS=$(date '+%Y-%m-%d %H:%M:%S')

  case $((i % 17)) in
    # Known malicious IP attempt
    0) echo "[$TS] [HTTP] GET /api/auth/login → 401"
       echo "[$TS] [HTTP] GET /api/admin/clients → 403"
       echo "[$TS] [SECURITY] threat-intel: IP 8.8.8.8 matched malicious-ips list" >> /var/technium/logs/app.log ;;
    # SQL injection attempt
    1) echo "[$TS] [HTTP] GET /api/admin/produits?id=1%20OR%201=1 → 500"
       echo "[$TS] [SECURITY] threat-intel: SQL injection signature detected from 10.0.0.7" >> /var/technium/logs/app.log ;;
    # C2 communication
    2) echo "[$TS] [SECURITY] threat-intel: outbound connection to pastebin.com detected (data exfil)" >> /var/technium/logs/app.log ;;
    # Credential stuffing
    3) for a in 1 2 3 4 5 6 7 8 9 10 11 12; do
         echo "[$TS] [HTTP] POST /api/auth/login → 401"
       done
       echo "[$TS] [SECURITY] threat-intel: credential stuffing detected - 12 failures in 60s" >> /var/technium/logs/app.log ;;
    # Brute force on admin
    4) echo "[$TS] [SECURITY] threat-intel: brute-force against admin@technium.sn from 185.220.101.1" >> /var/technium/logs/app.log ;;
    # XSS
    5) echo "[$TS] [SECURITY] threat-intel: XSS payload detected in request /api/public/devis" >> /var/technium/logs/app.log ;;
    # Suspicious User-Agent
    6) echo "[$TS] [SECURITY] threat-intel: scanner detected - User-Agent: sqlmap/1.7" >> /var/technium/logs/app.log ;;
    # Port scan detection
    7) echo "[$TS] [SECURITY] threat-intel: port scan detected from 91.219.236.1 - 500 ports in 10s" >> /var/technium/logs/app.log ;;
    # Data exfiltration via encoded payload
    8) echo "[$TS] [HTTP] POST /api/public/devis"
       echo "[$TS] [SECURITY] threat-intel: base64-encoded payload in POST body suspected exfiltration" >> /var/technium/logs/app.log ;;
    # CIF - correspondance liste sanctions ONU (regle 100400)
    9) echo "{\"event_type\":\"filtrage_sanctions\",\"mode\":\"ONU_consolidated\",\"source\":\"scsanctions.un.org\",\"subject\":\"ABDOU YAYA\",\"result\":\"MATCH\"}" >> /var/technium/logs/app.log ;;
    # CIF - transfert vers entite sanctionnee -> bloquee (regle 100401)
    10) echo "{\"event_type\":\"virement\",\"customer_id\":\"CI100091\",\"beneficiary\":\"ORGANISATION ALPHA\",\"amount\":\"500000\",\"sanctioned\":\"yes\",\"result\":\"REJECTED\"}" >> /var/technium/logs/app.log ;;
    # CIF - PEP detectee (regle 100402) + correspondance partielle (regle 100403)
    11) echo "{\"event_type\":\"filtrage_personnes\",\"subject\":\"MAMADOU TOURE\",\"result\":\"PEP_HIT\",\"source\":\"GIABA\"}" >> /var/technium/logs/app.log
        echo "{\"event_type\":\"filtrage_sanctions\",\"mode\":\"ONU\",\"subject\":\"IBRAHIM KADER\",\"matched_name\":\"IBRAHIM KADDER\",\"result\":\"FUZZY\"}" >> /var/technium/logs/app.log ;;
    # CIF - seuil declaratif depasse (regle 100404) + pays a risque (regle 100405)
    12) echo "{\"event_type\":\"declaration_threshold\",\"customer_id\":\"CI555001\",\"amount\":\"11000000\",\"result\":\"EXCEEDED\"}" >> /var/technium/logs/app.log
        echo "{\"event_type\":\"transfert\",\"customer_id\":\"CI444002\",\"country\":\"SY\",\"amount\":\"500000\",\"result\":\"REVIEWED\",\"risk_country\":\"yes\"}" >> /var/technium/logs/app.log ;;
    # CIF - mise a jour liste ONU (regle 100407)
    13) echo "{\"event_type\":\"liste_sanctions_update\",\"source\":\"scsanctions.un.org\",\"records\":\"3231\",\"result\":\"OK\"}" >> /var/technium/logs/app.log ;;
    # Securite SI - echec d'authentification (regle 100410) + elevation de privileges (regle 100411)
    14) echo "{\"event_type\":\"auth_failure\",\"user\":\"tsc\",\"src_ip\":\"10.0.0.9\",\"result\":\"FAILED\"}" >> /var/technium/logs/app.log
        echo "{\"event_type\":\"privilege_escalation\",\"user\":\"op_backoffice_7\",\"target\":\"sudo_root\",\"result\":\"GRANTED\"}" >> /var/technium/logs/app.log ;;
    # Piste d'audit - degradation du journal (regle 100418) + mode degrade (regle 100413)
    15) echo "{\"event_type\":\"audit_tamper\",\"record\":\"journal.jsonl\",\"user\":\"root\",\"result\":\"REWRITE\"}" >> /var/technium/logs/app.log
        echo "{\"event_type\":\"degraded_mode\",\"component\":\"guichet\",\"result\":\"ACTIVATED\"}" >> /var/technium/logs/app.log ;;
    # Conformite - PPE en retard (regle 100420) + consolidation multi-comptes (regle 100422)
    16) echo "{\"event_type\":\"ppe_evaluation\",\"subject\":\"ONOMO Ibrahima\",\"due_date\":\"2026-08-31\",\"result\":\"LATE\"}" >> /var/technium/logs/app.log
        echo "{\"event_type\":\"consolidation_multi_compte\",\"customer_id\":\"C-1029\",\"cumul_7j\":\"1850000\",\"result\":\"ALERT\"}" >> /var/technium/logs/app.log ;;
  esac

  if [ $(wc -l < /var/technium/logs/app.log) -gt 500 ]; then
    tail -200 /var/technium/logs/app.log > /var/technium/logs/app.log.tmp && mv /var/technium/logs/app.log.tmp /var/technium/logs/app.log
  fi
  if [ $(wc -l < /var/technium/logs/requests.log) -gt 500 ]; then
    tail -200 /var/technium/logs/requests.log > /var/technium/logs/requests.log.tmp && mv /var/technium/logs/requests.log.tmp /var/technium/logs/requests.log
  fi

  sleep 4
done