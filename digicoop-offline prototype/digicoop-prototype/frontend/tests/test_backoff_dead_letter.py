"""
Preuve par le comportement (pas seulement par la documentation) que le
backoff et le dead-letter fonctionnent réellement. Avant ce test, ce
mécanisme était décrit dans le README et dans le schéma d'état, mais jamais
exercé par aucun test automatisé — un écart signalé lors de l'auto-évaluation
du prototype.

Portée volontairement limitée à la machine à états CÔTÉ TERMINAL (ce fichier
teste l'axe offline en isolation, comme `test_offline_only.py`) : le point
`/sync/push` est entièrement simulé par interception réseau Playwright
(`page.route`), pas appelé sur le vrai central. `test_end_to_end_sync.py`
couvre déjà, séparément, la preuve qu'une vraie réponse du central fait
progresser la file. Mélanger ici un vrai appel réseau après une phase
mockée s'est heurté à une limitation connue de l'interception CDP de
Playwright (une requête cross-origin `continue()`-ée après avoir été
`fulfill()`-ée sur la même URL peut échouer une vérification CORS que le
vrai serveur, lui, satisfait — vérifié indépendamment avec `curl`). D'où le
choix de simuler aussi la réponse de succès, en construisant une réponse
`{results: [...], server_time}` cohérente avec le contenu réel de la
requête envoyée par le terminal.

Paramètres de backoff/dead-letter réduits à quelques centaines de ms via
`window.__DIGICOOP_TEST_SYNC_CONFIG__` (seam de test lu par App.jsx — voir
sa définition — qui ne change RIEN au comportement de production par défaut).
"""
import json
import time

from playwright.sync_api import sync_playwright

TEST_SYNC_CONFIG = {
    "maxAttempts": 2,
    "backoffStepsMs": [300],
    "deadLetterAgeMs": 3_600_000,  # volontairement énorme : on isole l'effet de maxAttempts
    "pushIntervalMs": 500,
    "pullIntervalMs": 5000,
    "batchSize": 50,
}
INIT_SCRIPT = f"window.__DIGICOOP_TEST_SYNC_CONFIG__ = {json.dumps(TEST_SYNC_CONFIG)};"

state = {"block_push": True}
errors = []


def handle_push_route(route):
    if state["block_push"]:
        route.fulfill(status=500, body="forced failure for backoff/dead-letter test")
        return
    # Réseau "réparé" : on simule un central qui accuse réception de tout,
    # en réutilisant les uuids réellement envoyés par le terminal (pas des
    # valeurs inventées) pour rester fidèle au contrat schemas.PushResponse.
    body = json.loads(route.request.post_data or "{}")
    items = body.get("items", [])
    results = [{"uuid": it["uuid"], "status": "synced", "detail": None} for it in items]
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"results": results, "server_time": "2026-01-01T00:00:00"}),
    )


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.add_init_script(INIT_SCRIPT)
    page.route("**/sync/push", handle_push_route)

    page.goto("http://127.0.0.1:4173/", wait_until="networkidle")

    page.wait_for_selector("text=Terminal verrouillé", timeout=10000)
    pin_inputs = page.query_selector_all("input[type=password]")
    pin_inputs[0].fill("1234")
    pin_inputs[1].fill("1234")
    page.click("button[type=submit]")
    page.wait_for_selector("text=Terminal agent", timeout=10000)
    print("PAGE LOADED — /sync/push simulé en échec, maxAttempts=2, backoff~300ms")

    page.fill("input[required]", "Ibrahima Sory Kaba")
    inputs = page.query_selector_all("input:not([type=password])")
    inputs[1].fill("3000000")  # montant élevé -> alerte en plus du client/transaction (3 entrées en file)
    page.click("button[type=submit]")
    page.wait_for_timeout(500)
    print("CLIENT CREATED, entries enqueued")

    # Attend la transition PENDING -> échecs avec backoff -> DEAD_LETTER.
    deadline = time.time() + 20
    reached_dead_letter = False
    while time.time() < deadline:
        body_text = page.inner_text("body")
        if "à renvoyer manuellement" in body_text:
            reached_dead_letter = True
            break
        page.wait_for_timeout(400)

    assert reached_dead_letter, "Les entrées n'ont jamais atteint dead_letter malgré l'échec simulé du push"
    dead_letter_line = [l for l in page.inner_text("body").split("\n") if "renvoyer manuellement" in l]
    print("DEAD_LETTER TRANSITION CONFIRMED:", dead_letter_line)

    # Le réseau "redevient fonctionnel" côté /sync/push, puis renvoi manuel.
    state["block_push"] = False
    # Sélecteur restreint au bouton : "text=Renvoyer" seul matcherait d'abord
    # le span "à renvoyer manuellement" (substring insensible à la casse).
    page.click("button:has-text('Renvoyer')")
    print("MANUAL REQUEUE CLICKED (retryDeadLetterEntries)")

    deadline = time.time() + 20
    recovered = False
    while time.time() < deadline:
        body_text = page.inner_text("body")
        if "à renvoyer manuellement" not in body_text and "en attente" not in body_text:
            recovered = True
            break
        page.wait_for_timeout(400)

    assert recovered, "Le renvoi manuel n'a jamais permis à la file de se vider une fois le réseau réparé"
    print("QUEUE FULLY DRAINED AFTER MANUAL REQUEUE : OK")

    browser.close()

if errors:
    print("PAGE ERRORS:", errors)
    raise SystemExit(1)

print("BACKOFF + DEAD_LETTER + MANUAL REQUEUE, VÉRIFIÉ CÔTÉ TERMINAL : OK")
