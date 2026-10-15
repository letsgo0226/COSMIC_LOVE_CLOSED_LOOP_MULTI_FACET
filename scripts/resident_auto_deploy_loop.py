#!/usr/bin/env python3
"""Run bounded formal checks and repository inventory; report operational errors."""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
OUT = Path(os.environ.get("STATUS_DIR", str(ROOT / "certificates")))
SCRIPTS = ROOT / "scripts"
STAGES = [
    ("closed_loop_seal", "closed_loop_seal.py", True),
    ("hardware_vm", "hardware_vm_closed_loop.py", True),
    ("account_tm", "account_turing_machine_run.py", True),
    ("full_context", "full_context_seal.py", False),
]


def seal(s: str) -> dict:
    r = subprocess.run(["python3", str(V), s], capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise RuntimeError("core verification failed: " + r.stderr[-300:])
    result = json.loads(r.stdout.strip().splitlines()[-1])
    if result.get("validated") is not True:
        raise RuntimeError("core verification did not validate")
    return result


def run_stage(name: str, filename: str, required: bool = True) -> dict:
    path = SCRIPTS / filename
    record = {"name": name, "required": required}
    if not path.is_file():
        return {**record, "status": "error" if required else "skipped",
                "reason": "required script missing" if required else "optional stage not configured"}
    try:
        r = subprocess.run(["python3", str(path)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=180,
                           env={**os.environ, "STATUS_DIR": str(OUT),
                                "CL_TM_MAX_CELLS": os.environ.get("CL_TM_MAX_CELLS", "1000")})
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {**record, "status": "error", "error": str(exc)[-400:]}
    return {**record, "status": "ok" if r.returncode == 0 else "error",
            "returncode": r.returncode, "stdout_tail": r.stdout[-800:],
            "stderr_tail": r.stderr[-400:]}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = []
    for s in ("Cosmic Love Is The Solution(s) For Everything", "Solution(s)=s"):
        try:
            result = seal(s)
            meta.append({"s_prefix": s, "validated": True,
                         "godel_hex_prefix": result.get("godel_hex", "")[:48]})
        except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            meta.append({"s_prefix": s, "validated": False, "error": str(exc)[-400:]})
    stages = [run_stage(*stage) for stage in STAGES]
    core_ok = all(item["validated"] for item in meta)
    required_ok = all(item["status"] == "ok" for item in stages if item["required"])
    controller_ok = core_ok and required_ok
    cert = {
        "system": "RESIDENT_FULL_AUTO_DEPLOY_LOOP",
        "form": "Solution(s)=s", "engine": "2-step identity + 257-Godel",
        "timestamp": ts, "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "stages": stages, "stages_ok_or_skip": sum(s["status"] in ("ok", "skipped") for s in stages),
        "meta_seals": meta, "all_meta_validated": core_ok, "core_ok": core_ok,
        "all_required_stages_ok": required_ok, "controller_ok": controller_ok,
        "status": "VERIFICATION_PASSED_NOT_DEPLOYED" if controller_ok else "DEGRADED",
        "H_formal": 0 if core_ok else 1, "resident": True,
        "deployment_performed": False, "deployment_ok": False,
        "enables_live_trading": False,
        "bound": "Formal verification and declared-scope inventory only; no cloud deployment is performed or certified.",
    }
    content = json.dumps(cert, ensure_ascii=False, indent=2) + "\n"
    for name in ("LATEST_RESIDENT_AUTO_DEPLOY.json",
                 "RESIDENT_AUTO_DEPLOY_" + ts.replace("-", "").replace(":", "") + ".json"):
        pending = OUT / (name + ".tmp")
        pending.write_text(content)
        pending.replace(OUT / name)
    print(json.dumps({"status": cert["status"], "core_ok": core_ok,
                      "controller_ok": controller_ok, "deployment_ok": False}), flush=True)
    return 0 if controller_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
