
"""
Push sender using Web Push / VAPID.

Dependencies:
    pip install pywebpush

Environment variables:
    VAPID_PRIVATE_KEY
    VAPID_PUBLIC_KEY
    VAPID_SUBJECT=mailto:you@example.com

Generate keys with an external VAPID-capable tool/library before deployment.
Do NOT commit the private key.
"""
from __future__ import annotations
import os, json
from pywebpush import webpush, WebPushException
from push_store import all_active, deactivate

def send_push(title: str, body: str, url: str):
    private=os.environ.get("VAPID_PRIVATE_KEY")
    subject=os.environ.get("VAPID_SUBJECT")
    if not private or not subject:
        raise RuntimeError("VAPID_PRIVATE_KEY/VAPID_SUBJECT missing")
    payload=json.dumps({"title":title,"body":body,"url":url},ensure_ascii=False)
    for sub in all_active():
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=private,
                vapid_claims={"sub":subject},
            )
        except WebPushException as e:
            status=getattr(getattr(e,"response",None),"status_code",None)
            if status in (404,410):
                deactivate(sub.get("endpoint",""))
            else:
                print("push error:", e)
