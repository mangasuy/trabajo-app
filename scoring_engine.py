
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROFILE=json.loads((ROOT/"search_profile.json").read_text(encoding="utf-8"))

def classify_offer(offer: dict) -> dict:
    text=" ".join(str(offer.get(k,"")) for k in ("title","description","location","schedule","requirements","salary")).lower()
    reasons=[]
    # Hard blocks explicitly agreed.
    hard_patterns = {
      "turno nocturno": ["turno nocturno","horario nocturno","trabajo nocturno"],
      "libreta obligatoria": ["libreta de conducir excluyente","libreta de conducir obligatoria","libreta cat. a excluyente"],
      "moto/vehículo obligatorio": ["moto propia excluyente","vehículo propio excluyente","vehiculo propio excluyente"],
      "inglés avanzado obligatorio": ["inglés avanzado excluyente","ingles avanzado excluyente","inglés avanzado obligatorio"],
      "título universitario obligatorio": ["título universitario excluyente","titulo universitario excluyente","título universitario obligatorio"],
    }
    for reason, pats in hard_patterns.items():
        if any(p in text for p in pats):
            return {**offer,"score":0,"decision":"discard","reasons":[reason]}
    loc=str(offer.get("location","")).lower()
    remote=bool(offer.get("remote"))
    if loc and not remote and "montevideo" not in loc:
        return {**offer,"score":0,"decision":"discard","reasons":["presencial fuera de Montevideo"]}

    # Conservative v1 score: never infer missing requirements.
    score=50
    title=str(offer.get("title","")).lower()
    primary=["administrativo","administrativa","asistente","back office","atención al cliente",
             "operador","soporte","e-commerce","ecommerce","wordpress","marketing digital",
             "community manager","contenido digital","cctv","monitoreo","videovigilancia",
             "portero","vigilante","auxiliar","recepción","recepcionista"]
    if any(x in title for x in primary):
        score += 25; reasons.append("puesto objetivo")
    if "montevideo" in loc or remote:
        score += 10; reasons.append("ubicación compatible")
    age=offer.get("age_hours")
    if age is not None:
        if age<=24: score+=10; reasons.append("publicada en últimas 24 h")
        elif age<=48: score+=5; reasons.append("publicada en últimas 48 h")
        else: return {**offer,"score":0,"decision":"discard","reasons":["más de 48 horas"]}
    sal=offer.get("salary_uyu")
    if sal is not None:
        if sal>=30000: score+=5; reasons.append("salario compatible")
        else: score=min(score,74); reasons.append("salario inferior a $30.000: revisar")
    score=max(0,min(100,score))
    decision="auto_apply" if score>=75 else "manual_review" if score>=50 else "discard"
    return {**offer,"score":score,"decision":decision,"reasons":reasons}

if __name__=="__main__":
    inp=ROOT/"data"/"buscojobs_latest.json"
    offers=json.loads(inp.read_text(encoding="utf-8")) if inp.exists() else []
    results=[classify_offer(o) for o in offers]
    out=ROOT/"data"/"buscojobs_scored.json"
    out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(results)} ofertas clasificadas -> {out}")
