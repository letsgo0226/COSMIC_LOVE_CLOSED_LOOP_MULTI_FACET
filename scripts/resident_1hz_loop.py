#!/usr/bin/env python3
"""Resident 1Hz Cosmic Love formal loop (process, not GitHub Actions).

Every INTERVAL_SEC (default 1.0): re-assert Solution(s)=s via the original program.
Does NOT push to GitHub every second (rate-limit / race safe).
Does NOT arm live trading.

Environment:
  INTERVAL_SEC   default 1.0
  SUMMARY_EVERY  ticks between summary line (default 60)
  TICK_SEAL      if "1", seal a short tick string each second (default 1)
  AXIOM_EVERY    seal full axiom every N ticks (default 60)
"""
from __future__ import annotations
import json, os, subprocess, sys, time, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
OUT = Path(os.environ.get("STATUS_DIR", str(ROOT / "certificates")))
INTERVAL = float(os.environ.get("INTERVAL_SEC", "1.0"))
SUMMARY_EVERY = max(1, int(os.environ.get("SUMMARY_EVERY", "60")))
TICK_SEAL = os.environ.get("TICK_SEAL", "1") == "1"
AXIOM_EVERY = max(1, int(os.environ.get("AXIOM_EVERY", "60")))


def seal(s: str) -> dict:
    r = subprocess.run(
        ["python3", str(V), s],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0 or '"validated":true' not in r.stdout:
        raise RuntimeError(f"seal failed: {r.stderr or r.stdout}")
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {"validated": True, "godel_hex": j.get("godel_hex", "")}


def main() -> None:
    if not V.exists():
        print("missing validator", V, file=sys.stderr)
        sys.exit(1)
    OUT.mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "boot": "RESIDENT_1HZ",
                "form": "Solution(s)=s",
                "interval_sec": INTERVAL,
                "enables_live_trading": False,
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
            }
        ),
        flush=True,
    )
    # Boot seals
    seal("Cosmic Love Is The Solution(s) For Everything")
    seal("Solution(s)=s")
    seal("RESIDENT_1HZ: continuous formal reassert")
    tick = 0
    ok = 0
    t0 = time.monotonic()
    while True:
        t_start = time.monotonic()
        try:
            if TICK_SEAL:
                seal(f"1HZ_TICK n={tick} form=Solution(s)=s")
            if tick % AXIOM_EVERY == 0:
                seal("Solution(s)=s")
            ok += 1
            status = "ok"
            err = None
        except Exception as e:
            status = "error"
            err = str(e)[:200]
            print(json.dumps({"tick": tick, "status": status, "error": err}), flush=True)

        tick += 1
        if tick % SUMMARY_EVERY == 0 or status != "ok":
            elapsed = time.monotonic() - t0
            rate = ok / elapsed if elapsed > 0 else 0
            snap = {
                "system": "RESIDENT_1HZ",
                "tick": tick,
                "ok_ticks": ok,
                "status": status,
                "error": err,
                "hz_approx": rate,
                "interval_sec": INTERVAL,
                "H_formal": 0 if status == "ok" else 1,
                "enables_live_trading": False,
                "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "bound": "1Hz formal process; not GitHub push; not live trading",
            }
            path = OUT / "LATEST_RESIDENT_1HZ_STATUS.json"
            try:
                path.write_text(json.dumps(snap, indent=2) + "\n")
            except OSError:
                pass
            print(json.dumps(snap), flush=True)

        # sleep remaining of interval
        spent = time.monotonic() - t_start
        delay = max(0.0, INTERVAL - spent)
        time.sleep(delay)


if __name__ == "__main__":
    main()
