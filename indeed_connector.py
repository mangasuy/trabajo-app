from __future__ import annotations
import json, re, html as htmlmod
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
BASE = "https://uy.indeed.com"

SEARCHES = [
    ("auxiliar administrativo", "Montevideo"),
    ("administrativo atención al cliente", "Montevideo"),
    ("recepcionista", "Montevideo"),
    ("telefonista", "Montevideo"),
    ("portero", "Montevideo"),
    ("guardia de seguridad", "Montevideo"),
    ("auxiliar", "Montevideo"),
]

def fetch(url):
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
        "Accept-Language": "es-UY,es;q=0.9,en;q=0.7",
    })
    with urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return " ".join(htmlmod.unescape(s).split()).strip()

def extract_jobs(page):
    out, seen = [], set()
    for m in re.finditer(r'href="([^"]*(?:viewjob\?jk=|clk\?jk=)[^"]+)"[^>]*>(.*?)</a>', page, re.I|re.S):
        href, inner = m.groups()
        title = clean(inner)
        if not title or len(title) < 3:
            continue
        url = urljoin(BASE, htmlmod.unescape(href))
        key = re.search(r"(?:jk=)([A-Za-z0-9]+)", url)
        kid = key.group(1) if key else url
        if kid in seen:
            continue
        seen.add(kid)
        out.append({"title": title, "url": url, "source": "Indeed Uruguay", "location": "Montevideo"})
    if not out:
        for m in re.finditer(r'<a[^>]+href="([^"]*jk=[^"]+)"[^>]*>(.*?)</a>', page, re.I|re.S):
            href, inner = m.groups()
            title = clean(inner)
            if 3 <= len(title) <= 180:
                url = urljoin(BASE, htmlmod.unescape(href))
                if url not in seen:
                    seen.add(url)
                    out.append({"title": title, "url": url, "source": "Indeed Uruguay", "location": "Montevideo"})
    return out

def main():
    path = DATA / "buscojobs_latest.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    all_jobs = list(existing)
    known = {(str(x.get("source","")), str(x.get("url",""))) for x in all_jobs}
    added = 0
    for query, location in SEARCHES:
        url = f"{BASE}/jobs?{urlencode({'q':query,'l':location,'fromage':2,'sort':'date'})}"
        try:
            page = fetch(url)
            for job in extract_jobs(page):
                key = (job["source"], job["url"])
                if key not in known:
                    known.add(key)
                    all_jobs.append(job)
                    added += 1
        except Exception as e:
            print("Indeed search error:", query, e)
    path.write_text(json.dumps(all_jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Indeed Uruguay: {added} candidatos nuevos agregados; total combinado {len(all_jobs)}")

if __name__ == "__main__":
    main()
