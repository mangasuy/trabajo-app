
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROFILE=json.loads((ROOT/"search_profile.json").read_text(encoding="utf-8"))

TARGETS={
 "administracion":["administrativo","administrativa","auxiliar administrativo","back office","backoffice","recepcionista","recepción","atención al cliente","cobranzas","facturación"],
 "digital":["e-commerce","ecommerce","wordpress","marketing digital","community manager","contenido digital","meta ads","seo","google analytics","automatización","automatizacion"],
 "seguridad":["cctv","monitoreo","videovigilancia","operador de cámaras","operador de camaras","portero","vigilante","control de acceso"],
 "auxiliares":["auxiliar","operador","soporte","atención al público","atencion al publico"]
}

HARD_REQUIRED = [
 ("libreta de conducir", ["libreta de conducir obligatoria","libreta de conducir excluyente","libreta cat. a excluyente"]),
 ("moto/vehículo propio", ["moto propia obligatoria","moto propia excluyente","vehículo propio obligatorio","vehiculo propio obligatorio","vehículo propio excluyente","vehiculo propio excluyente"]),
 ("inglés avanzado", ["inglés avanzado obligatorio","ingles avanzado obligatorio","inglés avanzado excluyente","ingles avanzado excluyente"]),
 ("título universitario", ["título universitario obligatorio","titulo universitario obligatorio","título universitario excluyente","titulo universitario excluyente"]),
 ("turno nocturno", ["turno nocturno","horario nocturno","medio turno noche","trabajo nocturno"])
]

REVIEW_ONLY_REQUIRED = [
 ("formación terciaria excluyente", ["formación terciaria excluyente","formacion terciaria excluyente","estudiante universitario excluyente","estudiante de facultad excluyente"]),
 ("software específico excluyente", ["memory fígaro excluyente","memory figaro excluyente","sap excluyente","erp excluyente"]),
 ("inglés requerido sin nivel claro", ["inglés oral y escrito","ingles oral y escrito","idioma inglés requisito","idioma ingles requisito"]),
 ("Excel intermedio/avanzado excluyente", ["excel nivel intermedio/avanzado (excluyente)","excel intermedio/avanzado excluyente","excel avanzado excluyente"])
]

def text_of(o):
    return " ".join(str(o.get(k,"")) for k in ("title","description","requirements","requirements_detected","education","schedule")).lower()

def classify(o):
    t=text_of(o); reasons=[]; warnings=[]
    # Age
    age=o.get("age_hours")
    if age is not None and age>48:
        return {**o,"score":0,"decision":"discard","reasons":["más de 48 horas"],"warnings":[]}
    # Geography
    loc=str(o.get("location","")).lower()
    remote=bool(o.get("remote"))
    if not remote and loc and "montevideo" not in loc:
        return {**o,"score":0,"decision":"discard","reasons":["presencial/híbrido fuera de Montevideo"],"warnings":[]}
    if remote and o.get("international") and not o.get("accepts_uruguay",False):
        return {**o,"score":0,"decision":"discard","reasons":["remoto internacional no confirma Uruguay"],"warnings":[]}

    # Hard exclusions only when explicitly obligatory/excluding.
    for label,pats in HARD_REQUIRED:
        if any(p in t for p in pats):
            return {**o,"score":0,"decision":"discard","reasons":[f"{label} obligatorio"],"warnings":[]}

    score=35

    title=str(o.get("title","")).lower()
    matched=[]
    for group,terms in TARGETS.items():
        if any(term in title or term in t for term in terms):
            matched.append(group)
    if "administracion" in matched: score+=25; reasons.append("experiencia administrativa/atención compatible")
    elif "digital" in matched: score+=25; reasons.append("perfil digital compatible")
    elif "seguridad" in matched: score+=22; reasons.append("experiencia CCTV/seguridad compatible")
    elif "auxiliares" in matched: score+=15; reasons.append("puesto auxiliar compatible")

    if "montevideo" in loc: score+=8; reasons.append("Montevideo")
    if remote: score+=8; reasons.append("remoto permitido")

    if age is not None:
        if age<=12: score+=12; reasons.append("muy reciente (≤12 h)")
        elif age<=24: score+=9; reasons.append("reciente (≤24 h)")
        else: score+=4; reasons.append("dentro de 48 h")

    # Education
    if any(x in t for x in ["secundaria completa","bachillerato completo","secundaria completo"]):
        score+=5; reasons.append("formación compatible")

    # Schedule
    if any(x in t for x in ["lunes a viernes","lunes a jueves"]) and not any(x in t for x in ["noche","nocturno"]):
        score+=5; reasons.append("jornada diurna prioritaria")
    if any(x in t for x in ["sábado","sabado","domingo"]):
        reasons.append("incluye fin de semana (aceptado, menor prioridad)")
        score-=2

    # Salary
    salary=o.get("salary_uyu")
    if salary is not None:
        if salary>=30000: score+=5; reasons.append("salario ≥ $30.000")
        else:
            score=min(score,74); warnings.append("salario menor a $30.000: revisar")

    # Missing or uncertain requirements that should block auto-apply but not discard.
    for label,pats in REVIEW_ONLY_REQUIRED:
        if any(p in t for p in pats):
            warnings.append(label)
            score=min(score,74)

    # Skill level safety: CV lists Microsoft Office, but does not explicitly prove advanced Excel.
    if re.search(r"excel.{0,25}(intermedio.?avanzado|avanzado).{0,25}excluyente", t) or re.search(r"excel.{0,25}excluyente.{0,25}(intermedio.?avanzado|avanzado)", t):
        warnings.append("Excel avanzado/intermedio-avanzado excluyente: validar manualmente")
        score=min(score,74)

    # Generic university requirement: if mandatory wording appears, discard; if desirable, lower.
    if re.search(r"(universitari[oa]|facultad|terciari[oa]).{0,35}(excluyente|obligatori[oa])",t):
        return {**o,"score":0,"decision":"discard","reasons":["formación universitaria/terciaria obligatoria"],"warnings":[]}
    if re.search(r"(universitari[oa]|facultad|terciari[oa]).{0,35}(deseable|valorará|valora)",t):
        score-=7; warnings.append("formación terciaria deseable")

    # Unknown explicit "excluyente": don't auto-apply if we cannot prove compliance.
    if "excluyente" in t and not any("compatible" in r for r in reasons):
        score=min(score,74); warnings.append("hay requisito excluyente que requiere validación")

    score=max(0,min(100,score))
    if warnings and score>=75:
        score=74
    decision="auto_apply" if score>=75 else "manual_review" if score>=50 else "discard"
    return {**o,"score":score,"decision":decision,"reasons":reasons,"warnings":warnings}

def main():
    files=[ROOT/"data"/"buscojobs_full.json", ROOT/"data"/"validation_offers.json"]
    inp=next((p for p in files if p.exists()),None)
    offers=json.loads(inp.read_text(encoding="utf-8")) if inp else []
    results=[classify(x) for x in offers]
    out=ROOT/"data"/"scored_results.json"
    out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(results)} ofertas clasificadas -> {out}")
    for x in results:
        print(f"{x['score']:>3}%  {x['decision']:<13}  {x.get('title','')}")
if __name__=="__main__": main()
