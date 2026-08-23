
"""
Safe application handoff.

Reads scored_results.json and opens only:
- manual_review offers, or
- auto_apply offers that still require user action.

No submission is performed.
"""
import json, webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"

def load():
    p=DATA/"scored_results.json"
    if not p.exists():
        p=DATA/"validation_results.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

def main():
    jobs=load()
    actionable=[j for j in jobs if j.get("decision") in ("manual_review","auto_apply") and j.get("url")]
    if not actionable:
        print("No hay ofertas con URL para abrir.")
        return
    for i,j in enumerate(actionable,1):
        print(f"{i}. {j.get('score')}% - {j.get('title')}")
    raw=input("Número de oferta para abrir (Enter cancela): ").strip()
    if not raw:
        return
    try:
        idx=int(raw)-1
        webbrowser.open(actionable[idx]["url"])
    except Exception:
        print("Selección inválida.")

if __name__=="__main__":
    main()
