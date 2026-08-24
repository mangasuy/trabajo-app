from __future__ import annotations

import html as htmlmod
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

BASE = "https://trabajo.gallito.com.uy"
SEARCH_PAGES = [
    f"{BASE}/buscar/fecha-publicacion/hace-2-dias/ubicacion/montevideo/page/1",
    f"{BASE}/buscar/fecha-publicacion/hace-2-dias/ubicacion/montevideo/page/2",
    f"{BASE}/buscar/fecha-publicacion/hace-2-dias/ubicacion/montevideo/page/3",
]

def fetch(url):
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126 Safari/537.36 TrabajoApp/1.0",
        "Accept-Language": "es-UY,es;q=0.9,en;q=0.7",
    })
    with urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")

def clean_html(s):
    s = re.sub(r"<script\b[^>]*>.*?</script>", " ", s or "", flags=re.I|re.S)
    s = re.sub(r"<style\b[^>]*>.*?</style>", " ", s, flags=re.I|re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return " ".join(htmlmod.unescape(s).split()).strip()

def parse_age_hours(text):
    m = re.search(r"Hace\s+(\d+)\s+minuto", text, re.I)
    if m:
        return max(0, int(m.group(1)) / 60)
    m = re.search(r"Hace\s+(\d+)\s+hora", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"Hace\s+(\d+)\s+d[ií]a", text, re.I)
    if m:
        return int(m.group(1)) * 24
    m = re.search(r"Hace\s+(\d+)\s+semana", text, re.I)
    if m:
        return int(m.group(1)) * 24 * 7
    if re.search(r"Hace\s+una?\s+hora", text, re.I):
        return 1
    if re.search(r"Hace\s+un\s+d[ií]a", text, re.I):
        return 24
    return None

def extract_h1(page):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.I|re.S)
    return clean_html(m.group(1)) if m else ""

def extract_company(page, title):
    text = clean_html(page)
    # Gallito suele colocar la empresa inmediatamente después del título.
    pos = text.lower().find(title.lower()) if title else -1
    if pos >= 0:
        tail = text[pos+len(title):].strip()
        # Evitar devolver textos de interfaz como empresa.
        candidate = re.split(r"\b(?:\d+\s+ofertas laborales|Hace\s+\d+|Postular|Responsabilidades)\b", tail, maxsplit=1, flags=re.I)[0].strip()
        if 1 < len(candidate) <= 90:
            return candidate
    return None

def detail(url):
    page = fetch(url)
    text = clean_html(page)
    title = extract_h1(page)
    if not title:
        return None
    return {
        "title": title,
        "company": extract_company(page, title),
        "url": url,
        "source": "Gallito Trabajo",
        "location": "Montevideo",
        "remote": bool(re.search(r"\b(remoto|teletrabajo|home office)\b", text, re.I)),
        "age_hours": parse_age_hours(text),
        "text": text,
    }

def main():
    urls = []
    seen = set()

    for search_url in SEARCH_PAGES:
        try:
            page = fetch(search_url)
        except Exception as e:
            print("Gallito search error:", search_url, e)
            continue

        for href in re.findall(r'href=["\']([^"\']*/anuncio/[^"\']+)["\']', page, re.I):
            url = urljoin(BASE, htmlmod.unescape(href))
            if url not in seen:
                seen.add(url)
                urls.append(url)

    jobs = []
    for url in urls[:60]:
        try:
            item = detail(url)
            if item:
                # La búsqueda ya viene filtrada por Montevideo y máximo 2 días.
                if item.get("age_hours") is None or item["age_hours"] <= 48:
                    jobs.append(item)
            time.sleep(0.15)
        except Exception as e:
            print("Gallito detail error:", url, e)

    out = DATA / "gallito_latest.json"
    out.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gallito Trabajo: {len(jobs)} ofertas de Montevideo (máx. 48 h) -> {out}")

if __name__ == "__main__":
    main()
