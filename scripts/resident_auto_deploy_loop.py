#!/usr/bin/env python3
"""Resident full-auto formal deployment loop.

Chains every Cosmic Love dimension/facet seal available in this repo into one
closed loop. The original program is the sole formal solver: Solution(s)=s.

Does NOT arm live trading or mutate Railway secrets.
"""
from __future__ import annotations
import json, os, subprocess, datetime, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
OUT = ROOT / "certificates"
SCRIPTS = ROOT / "scripts"

# Ordered resident stages (skip if missing)
STAGES = [
    ("closed_loop_seal", "closed_loop_seal.py"),
    ("hardware_vm", "hardware_vm_closed_loop.py"),
    ("account_tm", "account_turing_machine_run.py"),
    ("full_context", "full_context_seal.py"),  # may not exist in this repo
]


def seal(s: str) -> dict:
    r = subprocess.run(["python3", str(V), s], capture_output=True, text=True)
    if r.returncode != 0 or '"validated":true' not in r.stdout:
        raise SystemExit(f"core seal failed: {s!r}\n{r.stderr}")
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {
        "s": s,
        "validated": True,
        "s_hex": j.get("s_hex", ""),
        "godel_hex": j.get("godel_hex", ""),
    }


def run_stage(name: str, filename: str) -> dict:
    path = SCRIPTS / filename
    if not path.exists():
        return {"name": name, "status": "skipped", "reason": "missing"}
    r = subprocess.run(
        ["python3", str(path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**os.environ, "CL_TM_MAX_CELLS": os.environ.get("CL_TM_MAX_CELLS", "80")},
    )
    return {
        "name": name,
        "status": "ok" if r.returncode == 0 else "error",
        "returncode": r.returncode,
        "stdout_tail": (r.stdout or "")[-800:],
        "stderr_tail": (r.stderr or "")[-400:],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    stages = []
    for name, fn in STAGES:
        try:
            stages.append(run_stage(name, fn))
        except Exception as e:
            stages.append({"name": name, "status": "error", "error": str(e), "tb": traceback.format_exc()[-500:]})

    # Always seal resident meta + multi-facet self-description
    meta_seals = []
    for s in (
        "Cosmic Love Is The Solution(s) For Everything",
        "Solution(s)=s",
        "RESIDENT_AUTO_DEPLOY_LOOP: continuous formal redeploy of all facets",
        "DIMENSIONS: identity,evidence,governance,boundary,certificate,GlobalNoWar,hardware_as_VM,account_TM,GitHub_x_Railway",
        "FACETS: multi-facet closed loop under original Cosmic Love program",
        "BOUND: formal only; enables_live_trading=false",
        "",
        "The program is the solver. Resident loop reasserts Solution(s)=s.",
    ):
        meta_seals.append(
            {
                "s_prefix": s[:100],
                "validated": True,
                "godel_hex_prefix": seal(s).get("godel_hex", "")[:48],
            }
        )

    ok_stages = sum(1 for s in stages if s.get("status") in ("ok", "skipped"))
    cert = {
        "system": "RESIDENT_FULL_AUTO_DEPLOY_LOOP",
        "form": "Solution(s)=s",
        "engine": "2-step identity + 257-Godel (original Cosmic Love program)",
        "timestamp": ts,
        "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "stages": stages,
        "stages_ok_or_skip": ok_stages,
        "meta_seals": meta_seals,
        "H_formal": 0 if all(m["validated"] for m in meta_seals) else 1,
        "all_meta_validated": all(m["validated"] for m in meta_seals),
        "enables_live_trading": False,
        "resident": True,
        "automation": "GitHub Actions schedule + push + workflow_dispatch",
        "bound": (
            "Resident formal auto-deploy of Cosmic Love seals across dimensions/facets. "
            "Not Railway secret mutation, not Binance live arm, not physical unlimited hardware."
        ),
    }
    (OUT / "LATEST_RESIDENT_AUTO_DEPLOY.json").write_text(
        json.dumps(cert, ensure_ascii=False, indent=2) + "\n"
    )
    safe = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    (OUT / f"RESIDENT_AUTO_DEPLOY_{safe}.json").write_text(
        json.dumps(cert, ensure_ascii=False, indent=2) + "\n"
    )
    # Fail only if meta seals broken; stage errors recorded but loop still certifies formal core
    assert cert["all_meta_validated"]
    print("RESIDENT_AUTO_DEPLOY complete", ts)


if __name__ == "__main__":
    main()
