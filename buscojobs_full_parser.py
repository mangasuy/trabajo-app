from __future__ import annotations
import json, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

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
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 TrabajoApp/1.0",
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
    exact_bad = {"ver más ofertas","ver mas ofertas","ofertas por localización","ofertas por localizacion",
                 "ofertas por función laboral","ofertas por funcion laboral","cpa empleo"}
    if low in exact_bad:
        return False
    bad_phrases = ("ofertas de empleo esperan tu cv","ofertas por localización","ofertas por localizacion",
                   "ofertas por función laboral","ofertas por funcion laboral","ver más ofertas","ver mas ofertas")
    if any(x in low for x in bad_phrases):
        return False
    categories = ("administración","administracion","ventas","oficios","gestión","gestion","distribución","distribucion",
                  "tecnología de la información","tecnologia de la informacion","atención al cliente","atencion al cliente",
                  "contabilidad/auditorías","contabilidad/auditorias","producción","produccion","manufactura",
                  "atención médica","atencion medica","marketing","construcción","construccion","otro")
    for category in categories:
        if re.fullmatch(rf"{re.escape(category)}\s+\d+", low, flags=re.I):
            return False
    return not bool(re.fullmatch(r"[\d\s.,]+", t))

def extract(text, item):
    low = text.lower()
    def grab(pattern):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else None
    loc = item.get("location") or ("Montevideo" if "montevideo" in low else None)
    remote = bool(item.get("remote")) or any(x in low for x in ("teletrabajo","trabajo remoto","modalidad remota","100% remoto"))
    schedule = grab(r"Horario\s*[:\-]?\s*(.{3,120}?)(?:Puestos Vacantes|Requisitos|$)")
    education = grab(r"Estudio Mínimo Necesario\s*[:\-]?\s*(.{3,80}?)(?:Áreas de estudio|Conocimientos|Idiomas|$)")
    salary = None
    sm = re.search(r"\$\s*([0-9][0-9\.\,]{3,})", text)
    if sm:
        try:
            salary = int(re.sub(r"\D", "", sm.group(1)))
        except Exception:
            pass
    return {
        "title": item.get("title",""),
        "company": item.get("company"),
        "url": item.get("url",""),
        "source": item.get("source","Fuente laboral"),
        "location": loc,
        "remote": remote,
        "schedule": schedule,
        "education": education,
        "salary": salary,
        "age_hours": item.get("age_hours"),
        "published_at": item.get("published_at"),
        "text": text,
    }

def main():
    inp = DATA / "buscojobs_latest.json"
    jobs = json.loads(inp.read_text(encoding="utf-8")) if inp.exists() else []
    full = []
    for j in jobs[:80]:
        title = str(j.get("title","")).strip()
        url = str(j.get("url","")).strip()
        if not valid_job_title(title):
            print("Descartado:", title)
            continue
        if not url:
            continue
        try:
            txt = plain(fetch(url))
            if len(txt) < 180:
                continue
            full.append(extract(txt, j))
            time.sleep(0.20)
        except Exception as e:
            print("parse error:", j.get("source",""), title, str(e))
    out = DATA / "buscojobs_full.json"
    out.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(full)} fichas completas guardadas -> {out}")

if __name__ == "__main__":
    main()
