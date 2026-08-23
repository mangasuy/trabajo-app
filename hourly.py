
from __future__ import annotations
import os, json, hashlib, subprocess, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"
SUPABASE_URL=os.environ["SUPABASE_URL"].rstrip("/")
KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"]

def run(script):
    p=ROOT/script
    if p.exists():
        subprocess.run([sys.executable,str(p)],cwd=ROOT,check=False)

def oid(o):
    raw="|".join(str(o.get(k,"")).strip().lower() for k in ("source","url","title","company"))
    return hashlib.sha256(raw.encode()).hexdigest()[:24]

def request(path,method="GET",body=None,prefer=None):
    headers={"apikey":KEY,"Authorization":f"Bearer {KEY}","Content-Type":"application/json"}
    if prefer: headers["Prefer"]=prefer
    data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
    req=Request(f"{SUPABASE_URL}/rest/v1/{path}",data=data,headers=headers,method=method)
    try:
        with urlopen(req,timeout=30) as r:
            raw=r.read().decode()
            return json.loads(raw) if raw else None
    except HTTPError as e:
        print("Supabase",e.code,e.read().decode())
        raise

def exists(offer_id):
    rows=request(f"offers?id=eq.{offer_id}&select=id")
    return bool(rows)

def save(o):
    offer_id=oid(o)
    was=exists(offer_id)
    row={
      "id":offer_id,"source":o.get("source",""),"external_url":o.get("url"),
      "title":o.get("title",""),"company":o.get("company"),"location":o.get("location"),
      "score":int(o.get("score",0)),"decision":o.get("decision","discard"),
      "payload":o
    }
    request("offers?on_conflict=id","POST",[row],"resolution=merge-duplicates,return=minimal")
    if not was and row["decision"] in ("auto_apply","manual_review"):
        typ="apply_now" if row["decision"]=="auto_apply" else "review_now"
        verb="lista para postular" if typ=="apply_now" else "revisar ahora"
        msg=f'{row["score"]}% · {row["title"]} · {verb}'
        request("alerts","POST",[{"offer_id":offer_id,"type":typ,"message":msg}],"return=minimal")
    return not was

def main():
    run("buscojobs_connector.py")
    run("buscojobs_full_parser.py")
    run("scoring_engine_v2.py")
    candidates=[DATA/"scored_results.json",DATA/"validation_results.json"]
    p=next((x for x in candidates if x.exists()),None)
    if not p:
        raise SystemExit("No scored results")
    offers=json.loads(p.read_text(encoding="utf-8"))
    new=sum(save(o) for o in offers)
    print("New offers:",new)

if __name__=="__main__": main()
