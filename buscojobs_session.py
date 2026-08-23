
"""
Buscojobs session bootstrap — secure-ish local workflow.

Goal:
- Do NOT store email/password in this app.
- Open a real browser profile controlled by Playwright.
- User logs in manually once.
- Browser session/cookies remain in a local profile folder for reuse.

Install:
    pip install playwright
    playwright install chromium

Run:
    python buscojobs_session.py

This module DOES NOT click "postular" automatically yet.
It only creates/reuses an authenticated browser session.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
PROFILE_DIR = ROOT / ".browser_profiles" / "buscojobs"
HOME = "https://www.buscojobs.com.uy/"
FAQ = "https://www.buscojobs.com.uy/paginas/faq-postulantes"

def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print("Abriendo Buscojobs en una sesión persistente.")
    print("Si no estás logueado, iniciá sesión manualmente en el sitio.")
    print("La app no recibe ni guarda tu contraseña.")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(HOME, wait_until="domcontentloaded")
        print("Cuando hayas iniciado sesión y veas tu panel/perfil, podés cerrar la ventana.")
        page.wait_for_timeout(10**9)

if __name__ == "__main__":
    main()
