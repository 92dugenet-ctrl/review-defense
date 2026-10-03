"""V6.34 bounded staging smoke check. No destructive actions."""
from __future__ import annotations

# Contrôle HTTP de préproduction : interroge uniquement /health et /ready sur STAGING_BASE_URL.
# Il vérifie HTTPS, la version annoncée et l'état de disponibilité ; il ne crée ni ne modifie de données.
# Ce contrôle réseau est différent des tests automatisés et peut être appelé par une procédure de certification.

import json, os, sys, urllib.request

base = os.environ.get("STAGING_BASE_URL", "").rstrip("/")
if not base:
    print("STAGING_BASE_URL is required", file=sys.stderr)
    raise SystemExit(2)
if not base.startswith("https://"):
    print("STAGING_BASE_URL must use HTTPS", file=sys.stderr)
    raise SystemExit(2)

for path in ("/health", "/ready"):
    req = urllib.request.Request(base + path, headers={"Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        payload=json.loads(r.read().decode())
        print(path, r.status, payload)
        if path == "/health" and payload.get("version") != "6.34":
            raise SystemExit("unexpected application version")
        if path == "/ready" and payload.get("status") != "ready":
            raise SystemExit("staging is not ready")
