
from __future__ import annotations
import sqlite3, hashlib, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
import os
VOLUME_PATH = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or os.environ.get("DATA_DIR")
DB = (Path(VOLUME_PATH) / "trabajo.db") if VOLUME_PATH else (ROOT / "data" / "trabajo.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS offers (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    external_url TEXT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    score INTEGER NOT NULL,
    decision TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(status);
CREATE INDEX IF NOT EXISTS idx_offers_decision ON offers(decision);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id TEXT NOT NULL,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(offer_id) REFERENCES offers(id)
);
"""

def connect():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con

def make_offer_id(o: dict) -> str:
    source = str(o.get("source","")).strip().lower()
    url = str(o.get("url") or o.get("external_url") or "").strip().lower()
    title = str(o.get("title","")).strip().lower()
    company = str(o.get("company","")).strip().lower()
    raw = f"{source}|{url}|{title}|{company}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

def upsert_offer(o: dict):
    now = datetime.now(timezone.utc).isoformat()
    oid = make_offer_id(o)
    score = int(o.get("score",0))
    decision = o.get("decision","discard")
    with connect() as con:
        exists = con.execute("SELECT id,status FROM offers WHERE id=?", (oid,)).fetchone()
        if exists:
            con.execute("""UPDATE offers SET score=?, decision=?, last_seen=?, payload_json=? WHERE id=?""",
                        (score, decision, now, json.dumps(o,ensure_ascii=False), oid))
            return oid, False
        con.execute("""INSERT INTO offers
        (id,source,external_url,title,company,location,score,decision,status,first_seen,last_seen,payload_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (oid,o.get("source",""),o.get("url"),o.get("title",""),o.get("company"),
         o.get("location"),score,decision,"new",now,now,json.dumps(o,ensure_ascii=False)))
        return oid, True

def set_status(offer_id: str, status: str):
    allowed={"new","reviewing","applied","dismissed","manual_required"}
    if status not in allowed:
        raise ValueError("invalid status")
    with connect() as con:
        con.execute("UPDATE offers SET status=? WHERE id=?", (status, offer_id))

def create_alert(offer_id: str, kind: str, message: str):
    now=datetime.now(timezone.utc).isoformat()
    with connect() as con:
        # One unread alert of same type per offer.
        found=con.execute("SELECT id FROM alerts WHERE offer_id=? AND type=? AND read=0",
                          (offer_id,kind)).fetchone()
        if not found:
            con.execute("INSERT INTO alerts(offer_id,type,message,created_at) VALUES(?,?,?,?)",
                        (offer_id,kind,message,now))

def list_alerts():
    with connect() as con:
        rows=con.execute("""SELECT a.*,o.title,o.score,o.external_url,o.decision,o.status
                            FROM alerts a JOIN offers o ON o.id=a.offer_id
                            WHERE a.read=0 ORDER BY a.created_at DESC""").fetchall()
        return [dict(r) for r in rows]

def list_offers():
    with connect() as con:
        rows=con.execute("""SELECT id,source,external_url,title,company,location,score,decision,status,first_seen,last_seen
                            FROM offers ORDER BY first_seen DESC""").fetchall()
        return [dict(r) for r in rows]
