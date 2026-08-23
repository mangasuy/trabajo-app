
from __future__ import annotations
import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent.parent
import os
VOLUME_PATH=os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or os.environ.get("DATA_DIR")
DB=(Path(VOLUME_PATH)/"trabajo.db") if VOLUME_PATH else (ROOT/"data"/"trabajo.db")

def connect():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS push_subscriptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endpoint TEXT UNIQUE NOT NULL,
        subscription_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )""")
    return con

def save_subscription(sub: dict):
    endpoint=sub.get("endpoint")
    if not endpoint:
        raise ValueError("subscription endpoint missing")
    now=datetime.now(timezone.utc).isoformat()
    with connect() as con:
        con.execute("""INSERT INTO push_subscriptions(endpoint,subscription_json,created_at,active)
                       VALUES(?,?,?,1)
                       ON CONFLICT(endpoint) DO UPDATE SET
                       subscription_json=excluded.subscription_json, active=1""",
                    (endpoint,json.dumps(sub),now))

def all_active():
    with connect() as con:
        rows=con.execute("SELECT subscription_json FROM push_subscriptions WHERE active=1").fetchall()
    return [json.loads(r["subscription_json"]) for r in rows]

def deactivate(endpoint: str):
    with connect() as con:
        con.execute("UPDATE push_subscriptions SET active=0 WHERE endpoint=?", (endpoint,))
