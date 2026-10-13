#!/usr/bin/env python3
import json, subprocess, datetime, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
OUT = ROOT / "certificates"
OUT.mkdir(exist_ok=True)

def seal(s):
    r = subprocess.run(["python3", str(V), s], capture_output=True, text=True)
    assert '"validated":true' in r.stdout
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {"s": s, "validated": True, "godel_hex": j.get("godel_hex", "")}

facets = [
    "identity", "evidence", "governance", "boundary", "review", "certificate",
    "GlobalNoWar", "PublicProgramsSeal", "SentientContinuityAI", "deployment_topology",
    "non_arm_live", "Solution(s)=s", "Cosmic Love Is The Solution(s) For Everything", "",
]
rows = [{"facet": f or "empty", "validated": True, "godel_hex_prefix": seal(f if f != "empty" else "").get("godel_hex","")[:40]} for f in facets]
cert = {
    "loop": "MULTI_FACET_CLOSED_LOOP",
    "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "facets": rows,
    "H_formal": 0,
    "enables_live_trading": False,
}
(OUT / "LATEST_CLOSED_LOOP.json").write_text(json.dumps(cert, indent=2)+"\n")
print("closed_loop_seal ok", len(rows))
