import sys
from playwright.sync_api import sync_playwright

errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    page.goto("http://127.0.0.1:4173/", wait_until="networkidle")

    # Premier lancement (profil Playwright neuf, IndexedDB vide) : le terminal
    # demande de choisir un code pour chiffrer la base locale avant de continuer.
    page.wait_for_selector("text=Terminal verrouillé", timeout=10000)
    print("PIN GATE SHOWN (create mode) OK")
    pin_inputs = page.query_selector_all("input[type=password]")
    assert len(pin_inputs) == 2, "Le mode création doit proposer code + confirmation"
    pin_inputs[0].fill("1234")
    pin_inputs[1].fill("1234")
    page.click("button[type=submit]")

    page.wait_for_selector("text=Terminal agent", timeout=10000)
    print("PAGE LOADED OK")

    # Le backend n'est pas lancé ici : on vérifie que l'app reste utilisable
    # (chargement local de sql.js/IndexedDB, base déchiffrée en mémoire) même
    # sans réseau vers le central.
    page.wait_for_timeout(1500)
    status_text = page.inner_text("body")
    assert "hors-ligne" in status_text or "synchronisé" in status_text
    print("STATUS DOT OK:", "hors-ligne" in status_text)

    page.fill("input[required]", "Amadou Traore Diallo")
    inputs = page.query_selector_all("input:not([type=password])")
    inputs[1].fill("2500000")  # montant élevé -> doit déclencher une alerte par règle
    page.click("button[type=submit]")
    page.wait_for_timeout(500)

    result_text = page.inner_text("body")
    print("--- RESULT SNIPPET ---")
    idx = result_text.find("Amadou Traore Diallo")
    print(result_text[idx: idx + 400] if idx >= 0 else "NAME NOT FOUND")

    assert "Retenue" in result_text or "surveillance" in result_text, "L'alerte sur montant élevé n'a pas déclenché"
    print("RULE-BASED ALERT TRIGGERED OK")

    browser.close()

if errors:
    print("CONSOLE/PAGE ERRORS:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
else:
    print("NO CONSOLE ERRORS")
