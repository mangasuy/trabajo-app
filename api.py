
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json
from db import list_offers, list_alerts, set_status
from push_store import save_subscription

HOST="0.0.0.0"
PORT=8787

class Handler(BaseHTTPRequestHandler):
    def send_json(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/offers":
            return self.send_json(list_offers())
        if path=="/api/alerts":
            return self.send_json(list_alerts())
        if path=="/api/health":
            return self.send_json({"ok":True})
        if path=="/api/push-config":
            import os
            return self.send_json({"publicKey":os.environ.get("VAPID_PUBLIC_KEY","")})
        return self.send_json({"error":"not found"},404)

    def do_POST(self):
        path=urlparse(self.path).path
        if path=="/api/push/subscribe":
            length=int(self.headers.get("Content-Length","0"))
            payload=json.loads(self.rfile.read(length) or b"{}")
            try:
                save_subscription(payload)
                return self.send_json({"ok":True})
            except Exception as e:
                return self.send_json({"error":str(e)},400)
        if path.startswith("/api/offers/") and path.endswith("/status"):
            offer_id=path.split("/")[3]
            length=int(self.headers.get("Content-Length","0"))
            payload=json.loads(self.rfile.read(length) or b"{}")
            try:
                set_status(offer_id,payload.get("status",""))
                return self.send_json({"ok":True})
            except Exception as e:
                return self.send_json({"error":str(e)},400)
        return self.send_json({"error":"not found"},404)

if __name__=="__main__":
    print(f"API en http://127.0.0.1:{PORT}")
    HTTPServer((HOST,PORT),Handler).serve_forever()
