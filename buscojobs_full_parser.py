from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

OTHER_DEPARTMENTS = (
    "artigas","canelones","cerro largo","colonia","durazno","flores","florida",
    "lavalleja","maldonado","paysandú","paysandu","río negro","rio negro",
    "rivera","rocha","salto","san josé","san jose","soriano",
    "tacuarembó","tacuarembo","treinta y tres"
)

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, d):
        d = " ".join(d.split())
        if d:
            self.parts.append(d)

def fetch(url):
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126 Safari/537.36 TrabajoApp/1.0",
        "Accept-Language": "es-UY,es;q=0.9,en;q=0.7",
    })
    with urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")

def plain(html):
    p = TextParser()
    p.feed(html)
    return " ".join(p.parts)

def valid_job_title(title):
    if not title:
        return False
    t = " ".join(title.split()).strip()
    low = t.lower()
    exact_bad = {
        "ver más ofertas","ver mas ofertas","ofertas por localización","ofertas por localizacion",
        "ofertas por función laboral","ofertas por funcion laboral","cpa empleo"
    }
    if low in exact_bad:
        return False
    if any(x in low for x in ("ofertas de empleo esperan tu cv","ofertas por localización",
                              "ofertas por localizacion","ofertas por función laboral",
                              "ofertas por funcion laboral","ver más ofertas","ver mas ofertas")):
        return False
    if re.fullmatch(r"[\d\s.,]+", t):
        return False
    return True

def location_allowed(item):
    if item.get("remote"):
        return True
    loc = str(item.get("location") or "").strip().lower()
    if not loc:
        return True
    if "montevideo" in loc:
        return True
    return not any(dep in loc for dep in OTHER_DEPARTMENTS)

def extract(text, item):
    low = text.lower()

    def grab(pattern):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else None

    loc = item.get("location")
    if not loc and "montevideo" in low:
        loc = "Montevideo"

    remote = bool(item.get("remote")) or any(
        x in low for x in ("teletrabajo","trabajo remoto","modalidad remota","100% remoto","home office")
    )

    schedule = grab(r"Horario\s*[:\-]?\s*(.{3,120}?)(?:Puestos Vacantes|Requisitos|$)")
    education = grab(r"Estudio Mínimo Necesario\s*[:\-]?\s*(.{3,80}?)(?:Áreas de estudio|Conocimientos|Idiomas|$)")

    return {
        "title": item.get("title",""),
        "company": item.get("company"),
        "url": item.get("url",""),
        "source": item.get("source","Fuente laboral"),
        "location": loc,
        "remote": remote,
        "schedule": schedule,
        "education": education,
        "salary": item.get("salary"),
        "age_hours": item.get("age_hours"),
        "published_at": item.get("published_at"),
        "text": text,
    }

def load_json(path):
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

def main():
    jobs = []
    jobs.extend(load_json(DATA / "buscojobs_latest.json"))
    jobs.extend(load_json(DATA / "gallito_latest.json"))

    full = []
    seen = set()

    for j in jobs[:120]:
        title = str(j.get("title","")).strip()
        url = str(j.get("url","")).strip()

        if not valid_job_title(title) or not url:
            continue

        if not location_allowed(j):
            print("Descartado por departamento:", title, "|", j.get("location"))
            continue

        key = (str(j.get("source","")), url)
        if key in seen:
            continue
        seen.add(key)

        try:
            txt = str(j.get("text") or "").strip()
            if not txt:
                txt = plain(fetch(url))
                time.sleep(0.18)

            if len(txt) < 150:
                continue

            item = extract(txt, j)
            if not location_allowed(item):
                print("Descartado por departamento:", title, "|", item.get("location"))
                continue

            full.append(item)
        except Exception as e:
            print("parse error:", j.get("source",""), title, str(e))

    out = DATA / "buscojobs_full.json"
    out.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(full)} fichas completas combinadas -> {out}")

if __name__ == "__main__":
    main()
