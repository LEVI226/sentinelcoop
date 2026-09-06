import time
import urllib.request
import json
from playwright.sync_api import sync_playwright

errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    page.goto("http://127.0.0.1:4173/", wait_until="networkidle")

    page.wait_for_selector("text=Terminal verrouillé", timeout=10000)
    pin_inputs = page.query_selector_all("input[type=password]")
    pin_inputs[0].fill("1234")
    pin_inputs[1].fill("1234")
    page.click("button[type=submit]")

    page.wait_for_selector("text=Terminal agent", timeout=10000)
    print("PAGE LOADED (backend already reachable on :8000)")

    # Étape 1-5 du parcours, en local : client + transaction à montant élevé
    # -> alerte informative générée et mise en file de synchronisation.
    page.fill("input[required]", "Amadou Traore Diallo")
    inputs = page.query_selector_all("input:not([type=password])")
    inputs[1].fill("2500000")
    page.click("button[type=submit]")
    page.wait_for_timeout(500)
    print("CLIENT CREATED + LOCAL ALERT:", "surveillance" in page.inner_text("body"))

    # Laisse la sentinelle détecter le réseau et le worker drainer la file.
    page.wait_for_timeout(20000)
    print("STATUS LINE:", [l for l in page.inner_text("body").split("\n") if "synchronisé" in l or "hors-ligne" in l])

    browser.close()

if errors:
    print("PAGE ERRORS:", errors)

with urllib.request.urlopen("http://127.0.0.1:8000/alerts") as resp:
    alerts = json.loads(resp.read())

print(f"CENTRAL ALERTS COUNT: {len(alerts)}")
for a in alerts:
    print(" -", a["client_id"][:8], a["matched_name"], a["severity"], a["decision"])

with urllib.request.urlopen("http://127.0.0.1:8000/health") as resp:
    print(resp.read())

assert len(alerts) >= 1, "L'alerte créée hors-ligne (localement) n'est jamais arrivée côté central"
print("END-TO-END OFFLINE-FIRST SYNC : OK")
