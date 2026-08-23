
from __future__ import annotations
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
import json, os, threading, time, subprocess, sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"server"))
from db import list_offers, list_alerts, set_status
from push_store import save_subscription

PORT=int(os.environ.get("PORT","8080"))
HOST="0.0.0.0"

def run_pipeline():
    scripts=[
        ROOT/"buscojobs_connector.py",
        ROOT/"buscojobs_full_parser.py",
        ROOT/"scoring_engine_v2.py",
        ROOT/"server"/"pipeline.py",
    ]
    for script in scripts:
        if script.exists():
            print("[pipeline]", script.name, flush=True)
            subprocess.run([sys.executable,str(script)],cwd=ROOT,check=False)

def scheduler_loop():
    # First pass shortly after boot; then every hour.
    time.sleep(8)
    while True:
        try:
            run_pipeline()
        except Exception as e:
            print("[scheduler error]",e,flush=True)
        time.sleep(3600)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)

    def _json(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/health":
            return self._json({"ok":True,"service":"Trabajo","poll_minutes":60})
        if path=="/api/offers":
            return self._json(list_offers())
        if path=="/api/alerts":
            return self._json(list_alerts())
        if path=="/api/push-config":
            return self._json({"publicKey":os.environ.get("VAPID_PUBLIC_KEY","")})
        if path=="/":
            self.path="/index.html"
        return super().do_GET()

    def do_POST(self):
        path=urlparse(self.path).path
        length=int(self.headers.get("Content-Length","0"))
        try:
            payload=json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload={}
        if path=="/api/push/subscribe":
            try:
                save_subscription(payload)
                return self._json({"ok":True})
            except Exception as e:
                return self._json({"error":str(e)},400)
        if path.startswith("/api/offers/") and path.endswith("/status"):
            offer_id=path.split("/")[3]
            try:
                set_status(offer_id,payload.get("status",""))
                return self._json({"ok":True})
            except Exception as e:
                return self._json({"error":str(e)},400)
        return self._json({"error":"not found"},404)

if __name__=="__main__":
    threading.Thread(target=scheduler_loop,daemon=True).start()
    print(f"Trabajo escuchando en :{PORT}",flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
