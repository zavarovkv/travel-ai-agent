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
    print("[ERROR] N8N_API_KEY is not set")
    sys.exit(1)

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
            print("[INFO] n8n is ready")
            return
        except Exception:
            time.sleep(3)
    print("[ERROR] n8n did not become ready in time")
    sys.exit(1)


def sync() -> None:
    wait_for_n8n()

    existing = {
        w["name"]: w
        for w in api("GET", "/workflows?limit=100").get("data", [])
    }

    for path in sorted(WORKFLOWS_DIR.glob("*.json")):
        workflow = json.loads(path.read_text())
        name = workflow["name"]
        workflow.pop("id", None)
        workflow.pop("versionId", None)

        if name in existing:
            wf = existing[name]
            wf_id = wf["id"]
            # Preserve active status so we don't deactivate running workflows
            workflow["active"] = wf["active"]
            api("PUT", f"/workflows/{wf_id}", workflow)
            print(f"[UPDATE] '{name}' (id={wf_id}, active={wf['active']})")
        else:
            result = api("POST", "/workflows", workflow)
            print(f"[CREATE] '{name}' (id={result['id']})")


try:
    sync()
except urllib.error.HTTPError as e:
    print(f"[ERROR] n8n API {e.code}: {e.read().decode()}")
    sys.exit(1)
