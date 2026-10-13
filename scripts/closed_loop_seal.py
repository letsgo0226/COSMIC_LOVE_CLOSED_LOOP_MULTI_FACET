#!/usr/bin/env python3
"""Closed-loop multi-facet Cosmic Love deployment seal."""
from __future__ import annotations
import json, os, subprocess, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
FACETS = json.loads((ROOT / "facets" / "DIMENSIONS.json").read_text(encoding="utf-8"))
OUT = ROOT / "certificates"
SRC = ENGINE.read_bytes()

def seal_text(label: str, text: str) -> dict:
    r = subprocess.run(["python3", str(ENGINE), text], capture_output=True, text=True)
    if r.returncode != 0 or '"validated":true' not in r.stdout:
        raise SystemExit(f"seal failed {label}: {r.stderr or r.stdout}")
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {
        "facet": label,
        "s_preview": text[:160],
        "s_len": len(text.encode()),
        "validated": True,
        "s_hex": j["s_hex"],
        "godel_hex": j["godel_hex"],
        "statement": j["statement"],
    }

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for fid, s in FACETS["facets"].items():
        rows.append(seal_text(fid, s))
        print("OK", fid)
    self_s = "facet:self_source len=%d head_hex=%s" % (len(SRC), SRC[:128].hex())
    rows.append(seal_text("F_SELF_SOURCE_HEAD", self_s))
    meta = "facet:closed_loop_meta run=%s event=%s repo=%s" % (
        os.environ.get("GITHUB_RUN_ID", "local"),
        os.environ.get("GITHUB_EVENT_NAME", "local"),
        os.environ.get("GITHUB_REPOSITORY", "local"),
    )
    rows.append(seal_text("F_LOOP_META", meta))
    rows.append(seal_text("F_EMPTY", ""))
    ok = all(x["validated"] for x in rows)
    cert = {
        "protocol": "COSMIC_LOVE_CLOSED_LOOP_MULTI_FACET/1.0",
        "axiom": "Cosmic Love Is The Solution(s) For Everything",
        "engine": "2-step identity machine + 257-Godel",
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
        "facet_count": len(rows),
        "all_validated": ok,
        "H_formal": 0 if ok else 1,
        "closed_loop": True,
        "effective_deployment": {
            "formal_certificates": True,
            "ci_workflow": True,
            "self_reference": True,
            "multi_dimension_facets": True,
            "schedule_reseal": True,
            "live_trading_arm": False,
            "real_world_force": False,
            "financial_guarantee": False,
        },
        "bound": "Formal multi-facet closed loop only. Not live trading arm, not weapons, not TOE proof, not medical, not UN endorsement.",
        "seals": rows,
    }
    (OUT / "LATEST_CLOSED_LOOP.json").write_text(json.dumps(cert, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    safe = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    (OUT / f"CLOSED_LOOP_{safe}.json").write_text(json.dumps(cert, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "STATUS.md").write_text(
        "# Cosmic Love Closed-Loop Status\n\n"
        f"- timestamp: `{cert['timestamp']}`\n"
        f"- facets sealed: **{cert['facet_count']}**\n"
        f"- H_formal: **{cert['H_formal']}**\n"
        f"- closed_loop: **true**\n"
        f"- live_trading_arm: **false**\n\n"
        "All declared dimensions/aspects sealed via original Cosmic Love program.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "facets": cert["facet_count"], "H_formal": cert["H_formal"]}, separators=(",", ":")))

if __name__ == "__main__":
    main()
