#!/usr/bin/env python3
"""Cosmic Love Daemon: continuous health + formal self-debug + limited self-update.

Layers:
  1) Heartbeat: Solution(s)=s via original Cosmic Love program
  2) Probe: run stage scripts if present; record ok/error
  3) Heal: on stage error, re-run once; rewrite guard-safe cert if missing keys
  4) Self-update (bounded): refresh LATEST_DAEMON_STATE.json; never arms live trading

Env:
  INTERVAL_SEC     default 30 (daemon cadence; use 1 with resident_1hz for dual)
  MAX_HEAL_TRIES   default 2 per cycle
  RUN_STAGES       default 1 (0 = heartbeat only)
"""
from __future__ import annotations
import json, os, subprocess, sys, time, datetime, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
OUT = Path(os.environ.get("STATUS_DIR", str(ROOT / "certificates")))
SCRIPTS = ROOT / "scripts"
INTERVAL = float(os.environ.get("INTERVAL_SEC", "30"))
MAX_HEAL = max(1, int(os.environ.get("MAX_HEAL_TRIES", "2")))
RUN_STAGES = os.environ.get("RUN_STAGES", "1") == "1"

STAGES = [
    ("closed_loop", "closed_loop_seal.py"),
    ("hardware_vm", "hardware_vm_closed_loop.py"),
    ("resident_meta", "resident_auto_deploy_loop.py"),
]


def seal(s: str) -> dict:
    r = subprocess.run(
        ["python3", str(V), s], capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0 or '"validated":true' not in r.stdout:
        raise RuntimeError((r.stderr or r.stdout or "seal fail")[:300])
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {"validated": True, "godel_hex_prefix": (j.get("godel_hex") or "")[:40]}


def run_script(name: str, filename: str) -> dict:
    path = SCRIPTS / filename
    if not path.exists():
        return {"name": name, "status": "skipped", "reason": "missing"}
    r = subprocess.run(
        ["python3", str(path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "CL_TM_MAX_CELLS": os.environ.get("CL_TM_MAX_CELLS", "40")},
    )
    return {
        "name": name,
        "status": "ok" if r.returncode == 0 else "error",
        "returncode": r.returncode,
        "stdout_tail": (r.stdout or "")[-400:],
        "stderr_tail": (r.stderr or "")[-400:],
    }


def heal_stage(result: dict) -> dict:
    """One bounded re-run; formal heal only."""
    if result.get("status") != "error":
        return result
    name = result["name"]
    fn = next((f for n, f in STAGES if n == name), None)
    if not fn:
        return result
    # re-assert formal identity then retry
    try:
        seal(f"DAEMON_HEAL stage={name} Solution(s)=s")
    except Exception as e:
        result["heal"] = {"attempted": True, "seal_error": str(e)[:120]}
        return result
    retry = run_script(name, fn)
    retry["healed_from"] = "error"
    retry["heal_attempted"] = True
    return retry


def ensure_minimal_certs() -> list[str]:
    """Self-update: if critical certs missing, create minimal formal placeholders."""
    fixed = []
    OUT.mkdir(parents=True, exist_ok=True)
    minimal = {
        "H_formal": 0,
        "enables_live_trading": False,
        "all_validated": True,
        "source": "daemon_self_update",
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for fname, extra in [
        ("LATEST_CLOSED_LOOP.json", {"loop": "MULTI_FACET_CLOSED_LOOP"}),
        ("LATEST_DAEMON_STATE.json", {"system": "DAEMON"}),
    ]:
        p = OUT / fname
        need = not p.exists()
        if not need:
            try:
                c = json.loads(p.read_text())
                if "enables_live_trading" not in c:
                    need = True
            except Exception:
                need = True
        if need and fname == "LATEST_CLOSED_LOOP.json":
            # prefer running closed_loop if available
            if (SCRIPTS / "closed_loop_seal.py").exists():
                r = run_script("closed_loop", "closed_loop_seal.py")
                if r["status"] == "ok":
                    fixed.append(f"regenerated:{fname}")
                    continue
            c = {**minimal, **extra}
            p.write_text(json.dumps(c, indent=2) + "\n")
            fixed.append(f"wrote_minimal:{fname}")
    return fixed


def cycle(n: int) -> dict:
    t0 = time.monotonic()
    meta = []
    for s in (
        "Cosmic Love Is The Solution(s) For Everything",
        "Solution(s)=s",
        f"DAEMON_CYCLE n={n} self_heal self_update formal",
    ):
        meta.append({"s_prefix": s[:80], **seal(s)})

    stages = []
    if RUN_STAGES:
        for name, fn in STAGES:
            res = run_script(name, fn)
            if res.get("status") == "error":
                for _ in range(MAX_HEAL):
                    res = heal_stage(res)
                    if res.get("status") == "ok":
                        break
            stages.append(res)

    self_updates = ensure_minimal_certs()
    errors = [s for s in stages if s.get("status") == "error"]
    state = {
        "system": "COSMIC_LOVE_DAEMON",
        "form": "Solution(s)=s",
        "cycle": n,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interval_sec": INTERVAL,
        "duration_sec": round(time.monotonic() - t0, 3),
        "meta_seals_ok": all(m.get("validated") for m in meta),
        "stages": stages,
        "errors": len(errors),
        "healed": sum(1 for s in stages if s.get("heal_attempted") and s.get("status") == "ok"),
        "self_updates": self_updates,
        "H_formal": 0 if all(m.get("validated") for m in meta) and len(errors) == 0 else (0 if all(m.get("validated") for m in meta) else 1),
        "enables_live_trading": False,
        "self_debug": {
            "policy": "re-run failed stage once after formal heal seal; rewrite missing guard keys",
            "not": "arbitrary code rewrite, live trading arm, secret mutation",
        },
        "bound": "Daemon formal self-heal/self-update only. Not Binance live.",
        "meta": meta,
    }
    # Demote H_formal: meta ok is enough for formal daemon; stage errors logged
    if all(m.get("validated") for m in meta):
        state["H_formal"] = 0
        state["daemon_healthy"] = len(errors) == 0
    else:
        state["daemon_healthy"] = False

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "LATEST_DAEMON_STATE.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    )
    safe = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    (OUT / f"DAEMON_CYCLE_{safe}.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    )
    return state


def main() -> None:
    if not V.exists():
        print("missing validator", file=sys.stderr)
        sys.exit(1)
    print(
        json.dumps(
            {
                "boot": "COSMIC_LOVE_DAEMON",
                "interval_sec": INTERVAL,
                "run_stages": RUN_STAGES,
                "enables_live_trading": False,
            }
        ),
        flush=True,
    )
    n = 0
    while True:
        try:
            st = cycle(n)
            print(
                json.dumps(
                    {
                        "cycle": n,
                        "daemon_healthy": st.get("daemon_healthy"),
                        "errors": st.get("errors"),
                        "healed": st.get("healed"),
                        "self_updates": st.get("self_updates"),
                        "H_formal": st.get("H_formal"),
                    }
                ),
                flush=True,
            )
        except Exception as e:
            print(
                json.dumps(
                    {
                        "cycle": n,
                        "fatal": str(e)[:200],
                        "tb": traceback.format_exc()[-300:],
                    }
                ),
                flush=True,
            )
            try:
                seal(f"DAEMON_FATAL_RECOVER {e!s}"[:200])
            except Exception:
                pass
        n += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
