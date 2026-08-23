
from pathlib import Path
import json
from db import upsert_offer, create_alert
try:
    from push_sender import send_push
except Exception:
    send_push=None

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"

def run():
    candidates=[
        DATA/"scored_results.json",
        DATA/"validation_results.json",
        DATA/"buscojobs_scored.json"
    ]
    src=next((p for p in candidates if p.exists()),None)
    if not src:
        print("No hay resultados puntuados.")
        return
    offers=json.loads(src.read_text(encoding="utf-8"))
    created=0
    for o in offers:
        oid,is_new=upsert_offer(o)
        if not is_new:
            continue
        created+=1
        score=int(o.get("score",0))
        decision=o.get("decision","discard")
        title=o.get("title","Oferta")
        if decision=="auto_apply":
            msg=f"{score}% · {title} · lista para postular"
            create_alert(oid,"apply_now",msg)
            if send_push:
                try: send_push("Postular ahora",msg,o.get("url") or "/")
                except Exception as e: print("push no enviado:",e)
        elif decision=="manual_review":
            msg=f"{score}% · {title} · revisar ahora"
            create_alert(oid,"review_now",msg)
            if send_push:
                try: send_push("Oferta para revisar",msg,o.get("url") or "/")
                except Exception as e: print("push no enviado:",e)
        # discarded: intentionally silent
    print(f"Nuevas ofertas guardadas: {created}")

if __name__=="__main__":
    run()
