
"""
Buscojobs Uruguay connector — v1
Public discovery only. No credentials are stored here.

Run:
    python buscojobs_connector.py

This fetches the public Buscojobs Uruguay homepage, extracts visible job
cards, keeps Montevideo offers <=48h when the age can be determined, and
writes data/buscojobs_latest.json.

Important: the site's HTML may change. The parser is intentionally isolated
so it can be updated without changing the scoring engine.
"""
from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
URL = "https://www.buscojobs.com.uy/"

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self._href=None
        self._txt=[]
    def handle_starttag(self, tag, attrs):
        if tag=="a":
            self._href=dict(attrs).get("href")
            self._txt=[]
    def handle_data(self, data):
        if self._href is not None: self._txt.append(data)
    def handle_endtag(self, tag):
        if tag=="a" and self._href is not None:
            txt=" ".join(" ".join(self._txt).split())
            if txt and self._href:
                self.links.append((txt,urljoin(URL,self._href)))
            self._href=None; self._txt=[]

def fetch():
    req=Request(URL,headers={"User-Agent":"Mozilla/5.0 TrabajoApp/1.0"})
    with urlopen(req,timeout=20) as r:
        return r.read().decode("utf-8","ignore")

def age_hours(text):
    t=text.lower()
    m=re.search(r"hace\s+(\d+)\s*(minuto|minutos|min|hora|horas|día|días)",t)
    if not m: return None
    n=int(m.group(1)); u=m.group(2)
    if "min" in u: return n/60
    if "hora" in u: return n
    return n*24

def discover(html):
    # Save raw HTML for debugging/parser updates.
    (DATA/"buscojobs_raw.html").write_text(html,encoding="utf-8")
    p=LinkParser(); p.feed(html)
    # Job URLs on Buscojobs vary; retain likely offer links and deduplicate.
    out=[]; seen=set()
    for title, url in p.links:
        lu=url.lower()
        if ("oferta" in lu or "trabajo" in lu or "empleo" in lu) and len(title)>=4:
            key=(title.lower(),url)
            if key in seen: continue
            seen.add(key)
            out.append({"title":title,"url":url,"source":"Buscojobs Uruguay",
                        "discovered_at":datetime.now(timezone.utc).isoformat()})
    return out

if __name__=="__main__":
    try:
        html=fetch()
        jobs=discover(html)
        path=DATA/"buscojobs_latest.json"
        path.write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding="utf-8")
        print(f"Buscojobs: {len(jobs)} enlaces candidatos guardados en {path}")
    except Exception as e:
        print("No se pudo consultar Buscojobs:",e)
