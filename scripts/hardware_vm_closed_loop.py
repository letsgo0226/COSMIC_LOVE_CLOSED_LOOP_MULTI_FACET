#!/usr/bin/env python3
"""Hardware limits as VMs inside Solution(s) For Everything; multi-facet closed loop."""
from __future__ import annotations
import json, subprocess, datetime, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
FACETS = ROOT / "facets" / "HARDWARE_AS_VM.json"
OUT = Path(os.environ.get("STATUS_DIR", str(ROOT / "certificates")))


def seal(s: str) -> dict:
    r = subprocess.run(["python3", str(V), s], capture_output=True, text=True)
    if r.returncode != 0 or '"validated":true' not in r.stdout:
        raise SystemExit(f"fail {s!r}: {r.stderr}")
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {
        "s": s,
        "validated": True,
        "s_hex": j.get("s_hex", ""),
        "godel_hex": j.get("godel_hex", ""),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads(FACETS.read_text(encoding="utf-8"))
    seals = []
    # Core
    for s in (
        "Cosmic Love Is The Solution(s) For Everything",
        "Solution(s)=s",
        "HARDWARE_LIMITS_AS_VM: any device bound encoded as nested virtual machine facet",
        "",
    ):
        seals.append({"kind": "core", "seal": seal(s)})
    # Each hardware VM facet
    for f in spec["facets"]:
        seals.append({"kind": "hw_vm", "id": f["id"], "seal": seal(f["s"])})
    # Aggregate universal s (prefix of all facet ids)
    agg = "Solution(s) For Everything; hardware_as_VM; ids=" + ",".join(
        f["id"] for f in spec["facets"]
    )
    seals.append({"kind": "aggregate", "seal": seal(agg)})

    cert = {
        "loop": "HARDWARE_AS_VM_CLOSED_LOOP",
        "form": "Solution(s)=s",
        "engine": "2-step identity + 257-Godel",
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "model": spec["model"],
        "principle": spec["principle"],
        "facet_count": len(spec["facets"]),
        "all_validated": all(x["seal"]["validated"] for x in seals),
        "H_formal": 0,
        "enables_live_trading": False,
        "removes_physical_limits": False,
        "universal_validity": spec["universal_claim"],
        "non_claim": spec["non_claim"],
        "seals": [
            {
                "kind": x["kind"],
                "id": x.get("id"),
                "s_prefix": (x["seal"]["s"] or "")[:140],
                "validated": True,
                "godel_hex_prefix": (x["seal"].get("godel_hex") or "")[:40],
            }
            for x in seals
        ],
        "bound": (
            "Formal: hardware constraints internalized as VM facet strings with Solution(s)=s. "
            "Does not expand real CPU/RAM/energy. Railway continuous run still optional for formal s only."
        ),
    }
    (OUT / "LATEST_HARDWARE_VM_LOOP.json").write_text(
        json.dumps(cert, ensure_ascii=False, indent=2) + "\n"
    )
    safe = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    (OUT / f"HARDWARE_VM_LOOP_{safe}.json").write_text(
        json.dumps(cert, ensure_ascii=False, indent=2) + "\n"
    )
    print("HARDWARE_VM closed loop OK facets=", len(spec["facets"]))


if __name__ == "__main__":
    main()
