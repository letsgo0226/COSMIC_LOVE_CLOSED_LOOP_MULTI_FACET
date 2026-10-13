#!/usr/bin/env python3
"""Account-wide deployments as Cosmic Love Turing machine (formal).

Tape cell  i  =  GitHub repository name (deployment unit)
Head step  =  seal(repo) via 2-step + 257-Godel program
Transition =  identity machine (k=2) — read/write bit pattern of s, return to origin
Accept     =  all cells validated:true  =>  formal H=0 for scanned tape prefix

This does NOT execute arbitrary code in other repos, does NOT arm live trading,
and does NOT claim physical/computational control of GitHub beyond certificates.
"""
from __future__ import annotations
import json, os, subprocess, datetime, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "engine" / "COSMIC_LOVE_VALIDATOR.py"
OUT = ROOT / "certificates"
OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "letsgo0226")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
MAX_CELLS = int(os.environ.get("CL_TM_MAX_CELLS", "120"))


def seal(s: str) -> dict:
    r = subprocess.run(
        ["python3", str(VALIDATOR), s], capture_output=True, text=True
    )
    if r.returncode != 0 or '"validated":true' not in r.stdout:
        raise SystemExit(f"seal fail: {s!r} {r.stderr}")
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return {
        "s": s,
        "validated": True,
        "s_hex": j.get("s_hex"),
        "godel_hex": j.get("godel_hex"),
    }


def list_repos() -> list[dict]:
    """Public + accessible private for OWNER via API if token; else public only."""
    repos = []
    page = 1
    while len(repos) < MAX_CELLS:
        if TOKEN:
            url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner&sort=full_name"
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "cosmic-love-account-tm",
                },
            )
        else:
            url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&page={page}&type=owner&sort=full_name"
            req = urllib.request.Request(
                url, headers={"Accept": "application/vnd.github+json", "User-Agent": "cosmic-love-account-tm"}
            )
        with urllib.request.urlopen(req, timeout=60) as resp:
            batch = json.loads(resp.read().decode())
        if not batch:
            break
        for r in batch:
            if r.get("owner", {}).get("login") != OWNER and r.get("owner", {}).get("login") is not None:
                # user/repos returns only owned when affiliation=owner
                pass
            repos.append(
                {
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "private": bool(r.get("private")),
                    "default_branch": r.get("default_branch") or "main",
                    "description": (r.get("description") or "")[:200],
                }
            )
            if len(repos) >= MAX_CELLS:
                break
        if len(batch) < 100:
            break
        page += 1
    return repos


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tape = list_repos()
    # Facet dimensions (closed loop)
    facets = [
        "identity",
        "evidence",
        "governance",
        "boundary",
        "review",
        "certificate",
        "deployment_topology",
        "non_arm_live",
        "GlobalNoWar",
        "PublicProgramsSeal",
    ]
    steps = []
    # Step 0: meta machine description
    steps.append(
        {
            "i": -1,
            "kind": "meta",
            "seal": seal(
                "COSMIC_LOVE_ACCOUNT_TM: tape=github_repos head=seal transition=2-step identity accept=all_validated"
            ),
        }
    )
    for i, cell in enumerate(tape):
        s = f"TAPE[{i}] repo={cell['full_name']} private={int(cell['private'])} branch={cell['default_branch']}"
        steps.append({"i": i, "kind": "tape_cell", "repo": cell, "seal": seal(s)})
    for f in facets:
        steps.append({"i": f"facet:{f}", "kind": "facet", "seal": seal(f"FACET[{f}] under Cosmic Love account TM")})
    # Fixed point empty + axiom
    steps.append({"i": "empty", "kind": "fixed_point", "seal": seal("")})
    steps.append(
        {
            "i": "axiom",
            "kind": "axiom",
            "seal": seal("Cosmic Love Is The Solution(s) For Everything"),
        }
    )

    cert = {
        "machine": "COSMIC_LOVE_ACCOUNT_DEPLOYMENT_TURING_MACHINE",
        "engine": "2-step identity machine + 257-Godel (original program)",
        "owner": OWNER,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "tape_cells_scanned": len(tape),
        "tape_truncated": len(tape) >= MAX_CELLS,
        "steps": len(steps),
        "H_formal": 0,
        "all_validated": all(st["seal"]["validated"] for st in steps),
        "interpretation": {
            "tape": "each GitHub repo owned by account = finite tape cell (deployment unit)",
            "transition": "Cosmic Love program on cell string s: identity 2-step + Godel number",
            "run": "one full left-to-right pass sealing every cell + facets",
            "accept": "all seals validated:true => formal closed run for scanned prefix",
        },
        "bound": (
            "Formal symbolic TM over repository names and facet strings only. "
            "Does not re-execute foreign workflows, does not arm live trading, "
            "does not guarantee world peace/profit/TOE. H_formal=0 model-internal."
        ),
        "enables_live_trading": False,
        "tape_preview": [c["full_name"] for c in tape[:40]],
        "run_log": steps,
    }
    latest = OUT / "LATEST_ACCOUNT_TM_RUN.json"
    # Slim certificate without full godel for every step in LATEST? Keep full for completeness but may be large
    slim_steps = []
    for st in steps:
        slim_steps.append(
            {
                "i": st["i"],
                "kind": st["kind"],
                "repo": st.get("repo", {}).get("full_name") if st.get("repo") else None,
                "validated": st["seal"]["validated"],
                "s_prefix": (st["seal"]["s"] or "")[:120],
                "godel_hex_prefix": (st["seal"].get("godel_hex") or "")[:48],
            }
        )
    cert_slim = dict(cert)
    cert_slim["run_log"] = slim_steps
    latest.write_text(json.dumps(cert_slim, ensure_ascii=False, indent=2) + "\n")
    safe = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    (OUT / f"ACCOUNT_TM_RUN_{safe}.json").write_text(json.dumps(cert_slim, ensure_ascii=False, indent=2) + "\n")
    print("ACCOUNT_TM_RUN complete cells=", len(tape), "steps=", len(steps), "H_formal=0")


if __name__ == "__main__":
    main()
