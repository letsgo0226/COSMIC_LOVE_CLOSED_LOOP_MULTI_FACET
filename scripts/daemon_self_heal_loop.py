#!/usr/bin/env python3
"""Continuous formal verification with bounded retries and truthful health."""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
OUT = Path(os.environ.get("STATUS_DIR", str(ROOT / "certificates")))
SCRIPTS = ROOT / "scripts"
INTERVAL = max(1.0, float(os.environ.get("INTERVAL_SEC", "30")))
MAX_HEAL = max(1, min(3, int(os.environ.get("MAX_HEAL_TRIES", "2"))))
RUN_STAGES = os.environ.get("RUN_STAGES", "1") == "1"
STAGES = [
    ("closed_loop", "closed_loop_seal.py"),
    ("hardware_vm", "hardware_vm_closed_loop.py"),
    ("resident_meta", "resident_auto_deploy_loop.py"),
]


def seal(s: str) -> dict:
    r = subprocess.run(["python3", str(V), s], capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise RuntimeError("core verification failed: " + r.stderr[-300:])
    result = json.loads(r.stdout.strip().splitlines()[-1])
    if result.get("validated") is not True:
        raise RuntimeError("core verification did not validate")
    return {"validated": True, "godel_hex_prefix": result.get("godel_hex", "")[:40]}


def run_script(name: str, filename: str) -> dict:
    path = SCRIPTS / filename
    if not path.is_file():
        return {"name": name, "status": "error", "reason": "required script missing"}
    try:
        r = subprocess.run(["python3", str(path)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=300,
                           env={**os.environ, "STATUS_DIR": str(OUT),
                                "CL_TM_MAX_CELLS": os.environ.get("CL_TM_MAX_CELLS", "1000")})
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"name": name, "status": "error", "error": str(exc)[-400:]}
    return {"name": name, "status": "ok" if r.returncode == 0 else "error",
            "returncode": r.returncode, "stdout_tail": r.stdout[-400:],
            "stderr_tail": r.stderr[-400:]}


def heal_stage(result: dict) -> dict:
    if result.get("status") != "error":
        return result
    filename = next((fn for name, fn in STAGES if name == result["name"]), None)
    if filename is None:
        return result
    retry = run_script(result["name"], filename)
    return {**retry, "healed_from": "error", "heal_attempted": True}


def ensure_minimal_certs() -> list[str]:
    """Regenerate a checked certificate; never synthesize a passing placeholder."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "LATEST_CLOSED_LOOP.json"

    def valid():
        try:
            c = json.loads(path.read_text())
            return c.get("all_validated") is True and c.get("H_formal") == 0 and c.get("enables_live_trading") is False
        except (OSError, ValueError):
            return False

    if valid():
        return []
    result = run_script("closed_loop", "closed_loop_seal.py")
    if result["status"] == "ok" and valid():
        return ["regenerated:LATEST_CLOSED_LOOP.json"]
    return ["failed:LATEST_CLOSED_LOOP.json"]


def cycle(n: int) -> dict:
    started = time.monotonic()
    meta = []
    for s in ("Cosmic Love Is The Solution(s) For Everything", "Solution(s)=s"):
        try:
            meta.append({"s_prefix": s, **seal(s)})
        except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            meta.append({"s_prefix": s, "validated": False, "error": str(exc)[-300:]})
    stages = []
    if RUN_STAGES:
        for name, fn in STAGES:
            result = run_script(name, fn)
            for _ in range(MAX_HEAL):
                if result["status"] == "ok":
                    break
                result = heal_stage(result)
            stages.append(result)
    updates = ensure_minimal_certs() if RUN_STAGES else []
    errors = [s for s in stages if s.get("status") != "ok"]
    failed_certificates = [s for s in updates if s.startswith("failed:")]
    core_ok = all(m.get("validated") is True for m in meta)
    controller_ok = RUN_STAGES and core_ok and not errors and not failed_certificates
    healthy = core_ok and not errors and not failed_certificates
    now = datetime.datetime.now(datetime.timezone.utc)
    state = {
        "system": "COSMIC_LOVE_DAEMON", "form": "Solution(s)=s", "cycle": n,
        "release_commit": os.environ.get("RAILWAY_GIT_COMMIT_SHA", ""),
        "runtime_generation": os.environ.get("RUNTIME_GUARD_GENERATION", ""),
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "interval_sec": INTERVAL,
        "duration_sec": round(time.monotonic() - started, 3),
        "meta_seals_ok": core_ok, "core_ok": core_ok, "controller_ok": controller_ok,
        "daemon_healthy": healthy, "stages": stages, "errors": len(errors) + len(failed_certificates),
        "healed": sum(s.get("heal_attempted", False) and s["status"] == "ok" for s in stages),
        "self_updates": updates, "H_formal": 0 if core_ok else 1,
        "status": ("VERIFICATION_PASSED_NOT_DEPLOYED" if controller_ok else
                   "HEARTBEAT_ONLY" if healthy else "DEGRADED"),
        "deployment_performed": False, "deployment_ok": False,
        "enables_live_trading": False, "meta": meta,
        "self_debug": {"policy": "bounded retries; certificate regeneration requires actual successful verification"},
        "bound": "Formal verification and inventory daemon; cloud deployment and service health are not certified.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    content = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    for name in ("LATEST_DAEMON_STATE.json", "DAEMON_CYCLE_" + now.strftime("%Y%m%dT%H%M%SZ") + ".json"):
        pending = OUT / (name + ".tmp")
        pending.write_text(content)
        pending.replace(OUT / name)
    return state


def main() -> None:
    if not V.is_file():
        raise SystemExit("missing validator")
    print(json.dumps({"boot": "COSMIC_LOVE_DAEMON", "interval_sec": INTERVAL,
                      "run_stages": RUN_STAGES}), flush=True)
    n = 0
    while True:
        try:
            state = cycle(n)
            print(json.dumps({key: state[key] for key in (
                "cycle", "status", "daemon_healthy", "core_ok", "controller_ok",
                "deployment_ok", "errors", "healed", "H_formal")}), flush=True)
        except Exception as exc:
            print(json.dumps({"cycle": n, "status": "DEGRADED",
                              "daemon_healthy": False, "controller_ok": False,
                              "deployment_ok": False, "fatal": str(exc)[-300:]}), flush=True)
        n += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
