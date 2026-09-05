#!/usr/bin/env python3
"""Lit les alertes récentes indexées (par défaut les règles CIF 1004xx)."""
import json, urllib.request, ssl, base64, sys

prefix = sys.argv[1] if len(sys.argv) > 1 else "1003,1002,1001"
prefixes = tuple(prefix.split(","))

ctx = ssl._create_unverified_context()
req = urllib.request.Request(
    'https://localhost:9200/wazuh-alerts-*/_search?size=12&sort=@timestamp:desc',
    data=json.dumps({"_source": ["rule.id", "rule.level", "rule.description", "full_log"],
                     "query": {"match_all": {}}}).encode(),
    headers={'Content-Type': 'application/json',
             'Authorization': 'Basic ' + base64.b64encode(b'admin:SecretPassword123!').decode()})
d = json.load(urllib.request.urlopen(req, context=ctx))
found = 0
for h in d.get('hits', {}).get('hits', []):
    s = h['_source']
    rid = s.get('rule', {}).get('id', '')
    if rid.startswith(prefixes):
        rl = s.get('rule', {}).get('level')
        rd = s.get('rule', {}).get('description', '')
        fl = s.get('full_log', '')[:70]
        print(f'   - level {rl} | {rid}: {rd}')
        print(f'       log: {fl}')
        found += 1
print(f'{found} alertes UEMOA indexees (préfixes {prefix})')
if found == 0:
    print('AUCUNE trouvee - verifier wazuh-logtest ou filebeat')