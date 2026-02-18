#!/usr/bin/env python3
"""Sync n8n workflows from n8n-workflows/ via n8n Public API.

Runs after deploy. Creates missing workflows, updates existing ones by name.
Preserves the active/inactive status of already-running workflows.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

N8N_URL = os.environ.get("N8N_URL", "http://localhost:5678")
N8N_API_KEY = os.environ.get("N8N_API_KEY", "")
WORKFLOWS_DIR = Path(__file__).parent.parent / "n8n-workflows"

if not N8N_API_KEY:
    print("[WARN] N8N_API_KEY is not set — skipping workflow sync")
    print("[WARN] To enable: generate key in n8n UI → Settings → n8n API, add as GitHub Secret N8N_API_KEY")
    sys.exit(0)

HEADERS = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json",
}


def api(method: str, path: str, data: dict = None) -> dict:
    url = f"{N8N_URL}/api/v1{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def wait_for_n8n(timeout: int = 90) -> None:
    print(f"[INFO] waiting for n8n at {N8N_URL} ...")
    for _ in range(timeout // 3):
        try:
            urllib.request.urlopen(f"{N8N_URL}/healthz", timeout=2)
            # healthz can return 200 before the REST API is fully initialized
            time.sleep(5)
            print("[INFO] n8n is ready")
            return
        except Exception:
            time.sleep(3)
    print("[ERROR] n8n did not become ready in time")
    sys.exit(1)


ALLOWED_FIELDS = {"name", "nodes", "connections", "settings", "staticData"}


def to_api_body(workflow: dict) -> dict:
    """Strip fields not accepted by n8n API (active is read-only)."""
    return {k: v for k, v in workflow.items() if k in ALLOWED_FIELDS}


def resolve_credentials(body: dict, cred_map: dict) -> None:
    """Replace placeholder credential IDs with real IDs looked up by name."""
    for node in body.get("nodes", []):
        for cred_ref in node.get("credentials", {}).values():
            name = cred_ref.get("name")
            if name and name in cred_map:
                cred_ref["id"] = cred_map[name]


def sync() -> None:
    wait_for_n8n()

    # Build name → id map for all credentials in n8n
    cred_map = {
        c["name"]: c["id"]
        for c in api("GET", "/credentials").get("data", [])
    }
    if cred_map:
        print(f"[INFO] found credentials: {list(cred_map.keys())}")

    existing = {
        w["name"]: w
        for w in api("GET", "/workflows?limit=100").get("data", [])
    }

    for path in sorted(WORKFLOWS_DIR.glob("*.json")):
        workflow = json.loads(path.read_text())
        name = workflow["name"]
        body = to_api_body(workflow)
        resolve_credentials(body, cred_map)

        if name in existing:
            wf = existing[name]
            wf_id = wf["id"]
            api("PUT", f"/workflows/{wf_id}", body)
            # Restore active state via dedicated endpoint
            if wf["active"]:
                api("POST", f"/workflows/{wf_id}/activate")
            print(f"[UPDATE] '{name}' (id={wf_id}, active={wf['active']})")
        else:
            result = api("POST", "/workflows", body)
            print(f"[CREATE] '{name}' (id={result['id']})")


try:
    sync()
except urllib.error.HTTPError as e:
    print(f"[ERROR] n8n API {e.code}: {e.read().decode()}")
    sys.exit(1)
