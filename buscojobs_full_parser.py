from __future__ import annotations
import json,re,time
from pathlib import Path
from urllib.request import Request,urlopen
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; DATA.mkdir(exist_ok=True)
class TextParser(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,d):
        d=" ".join(d.split())
        if d:self.parts.append(d)
def fetch(url):
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 TrabajoApp/1.0"})
    with urlopen(req,timeout=20) as r:return r.read().decode("utf-8","ignore")
def plain(html):
    p=TextParser();p.feed(html);return " ".join(p.parts)
def extract(text,url,title):
    low=text.lower()
    def grab(pattern):
        m=re.search(pattern,text,re.I);return m.group(1).strip() if m else None
    loc="Montevideo" if "montevideo" in low else None
    remote=any(x in low for x in ["teletrabajo","trabajo remoto","modalidad remota","100% remoto"])
    schedule=grab(r"Horario\s+(.{3,120}?)(?:Puestos Vacantes|Requisitos|$)")
    education=grab(r"Estudio Mínimo Necesario\s+(.{3,80}?)(?:Áreas de estudio|Conocimientos|Idiomas|$)")
    salary=None
    sm=re.search(r"\$\s*([0-9][0-9\.\,]{3,})",text)
    if sm:
        try:salary=int(re.sub(r"\D","",sm.group(1)))
        except:pass
    req=[t for t in ["libreta de conducir","moto propia","vehículo propio","vehiculo propio","inglés avanzado","ingles avanzado","título universitario","titulo universitario","Memory Fígaro","formación terciaria","formacion terciaria"] if t.lower() in low]
    return {"title":title,"url":url,"source":"Buscojobs Uruguay","location":loc,"remote":remote,"schedule":schedule,"education":education,"salary_uyu":salary,"requirements_detected":req,"description":text[:12000]}
def main():
    inp=DATA/"buscojobs_latest.json"
    jobs=json.loads(inp.read_text(encoding="utf-8")) if inp.exists() else []
    full=[]
    for j in jobs[:40]:
        try:
            txt=plain(fetch(j["url"]))
            if len(txt)<250:continue
            full.append(extract(txt,j["url"],j["title"]));time.sleep(.25)
        except Exception as e:full.append({**j,"parse_error":str(e)})
    out=DATA/"buscojobs_full.json";out.write_text(json.dumps(full,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(full)} fichas completas guardadas -> {out}")
if __name__=="__main__":main()
