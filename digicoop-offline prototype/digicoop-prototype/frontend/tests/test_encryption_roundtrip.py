"""
Vérifie le chiffrement au repos (db/crypto.js) sur un vrai cycle de
fermeture/réouverture du navigateur — pas seulement à l'intérieur d'une
session ouverte. Utilise un profil Chromium persistant (contrairement aux
autres tests qui relancent un navigateur "vierge" à chaque fois) pour que
la base IndexedDB chiffrée survive réellement à la fermeture de l'onglet,
exactement comme sur le terminal d'un agent.

Trois temps :
  1. Première ouverture : création du code, un client saisi, fermeture.
  2. Réouverture avec le MAUVAIS code : doit échouer proprement (message
     "Code incorrect"), sans jamais afficher de terminal utilisable.
  3. Réouverture avec le BON code : doit déchiffrer et retrouver l'alerte
     locale générée à l'étape 1 — preuve que ce n'est pas juste un écran de
     façade, la donnée est réellement chiffrée puis réellement récupérable.
     (On vérifie la présence d'une ligne dans "Alertes locales" plutôt que
     le nom du client : AlertsList.jsx n'affiche que l'id tronqué du client,
     jamais son nom complet — voir ce fichier.)
"""
import shutil
import tempfile

from playwright.sync_api import sync_playwright

profile_dir = tempfile.mkdtemp(prefix="digicoop-profile-")

with sync_playwright() as p:
    # --- Étape 1 : première ouverture, création du code ---
    ctx = p.chromium.launch_persistent_context(profile_dir, headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("http://127.0.0.1:4173/", wait_until="networkidle")
    page.wait_for_selector("text=Terminal verrouillé", timeout=10000)
    pins = page.query_selector_all("input[type=password]")
    assert len(pins) == 2, "premier lancement attendu : mode création (code + confirmation)"
    pins[0].fill("secret-9182")
    pins[1].fill("secret-9182")
    page.click("button[type=submit]")
    page.wait_for_selector("text=Terminal agent", timeout=10000)

    page.fill("input[required]", "Fatoumata Kone Sangare")
    inputs = page.query_selector_all("input:not([type=password])")
    inputs[1].fill("2500000")  # montant élevé -> génère une alerte locale persistée
    page.click("button[type=submit]")
    assert "Fatoumata Kone Sangare" in page.inner_text("body")
    page.wait_for_timeout(1500)  # laisse le temps au persist() différé (debounce ~1s) de s'exécuter
    print("STEP 1 OK — client + alerte saisis, en attente de la persistance différée")
    ctx.close()

    # --- Étape 2 : réouverture avec un MAUVAIS code ---
    ctx = p.chromium.launch_persistent_context(profile_dir, headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("http://127.0.0.1:4173/", wait_until="networkidle")
    page.wait_for_selector("text=Terminal verrouillé", timeout=10000)
    pins = page.query_selector_all("input[type=password]")
    assert len(pins) == 1, "réouverture attendue : mode déverrouillage (un seul champ)"
    pins[0].fill("mauvais-code")
    page.click("button[type=submit]")
    page.wait_for_selector("text=incorrect", timeout=10000)
    assert "Terminal agent" not in page.inner_text("body"), "le terminal ne doit jamais s'ouvrir avec un mauvais code"
    print("STEP 2 OK — mauvais code rejeté proprement, terminal resté verrouillé")
    ctx.close()

    # --- Étape 3 : réouverture avec le BON code ---
    ctx = p.chromium.launch_persistent_context(profile_dir, headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("http://127.0.0.1:4173/", wait_until="networkidle")
    page.wait_for_selector("text=Terminal verrouillé", timeout=10000)
    pins = page.query_selector_all("input[type=password]")
    pins[0].fill("secret-9182")
    page.click("button[type=submit]")
    page.wait_for_selector("text=Terminal agent", timeout=10000)
    page.wait_for_timeout(500)
    body = page.inner_text("body")
    assert "Aucune alerte locale" not in body, "l'alerte générée avant fermeture doit être retrouvée après déchiffrement"
    assert "règle transactionnelle" in body, "l'alerte retrouvée doit être celle générée à l'étape 1 (règle montant élevé)"
    print("STEP 3 OK — bon code accepté, alerte locale retrouvée après un vrai cycle fermeture/réouverture")
    ctx.close()

shutil.rmtree(profile_dir, ignore_errors=True)
print("CHIFFREMENT AU REPOS — CYCLE COMPLET FERMETURE/RÉOUVERTURE VÉRIFIÉ : OK")
