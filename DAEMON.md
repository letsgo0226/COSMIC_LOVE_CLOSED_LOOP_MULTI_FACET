# Cosmic Love Daemon (self-heal + bounded self-update)

## What

A **daemon loop** that:

1. Reasserts `Solution(s)=s` (original Cosmic Love program)
2. Probes stage scripts (closed-loop, hardware-vm, resident meta)
3. **Self-debug / heal**: on stage failure → formal heal seal → one re-run
4. **Self-update (bounded)**: regenerate missing certs with guard keys (`enables_live_trading: false`)

## Cadence

| Host | Interval |
|------|----------|
| Railway daemon service | `INTERVAL_SEC` (default 30s) |
| GitHub Actions | every 6h + manual (cert snapshot to repo) |
| 1Hz process | separate service; pure heartbeat |

## Self-update scope

**In scope:** re-run seals, rewrite incomplete certificates, log heal attempts.  
**Out of scope:** live trading arm, mutating Binance secrets, unbounded code rewrite.

## Run

```bash
INTERVAL_SEC=30 python3 scripts/daemon_self_heal_loop.py
```
# Operational health repair — 2026-10-15

The daemon image includes `facets/`. All stages use `STATUS_DIR` for their
certificates. A required-stage error makes `controller_ok=false` and reports
`DEGRADED`, even when `core_ok=true` and the mathematical `H_formal=0`.
Missing certificates are regenerated only by a successful verifier; a passing
placeholder is never synthesized. The resident command exits nonzero on a
required-stage failure, and Actions retains the evidence on failure.

Repository discovery uses the owner-public endpoint for repository-scoped
`GITHUB_TOKEN`, the installation endpoint for an explicitly supplied App token,
or the authenticated-user endpoint for an explicitly supplied user token.
The certificate declares the visibility scope and truncation. Public inventory
does not certify private-account coverage. Daemon inventory is cached for ten
minutes to bound API traffic. Use `CL_TM_MAX_CELLS=1000` for the current account.

These commands report `deployment_ok=false`: they verify the core and inventory,
and do not deploy or check cloud releases. A cloud deployment needs its own
provider revision, terminal deployment result, and application health evidence.

## Railway runtime supervision

The Railway entry point is now:

```sh
python3 -u scripts/runtime_guard.py --kind daemon -- python3 -u scripts/daemon_self_heal_loop.py
```

The guard exposes `/health` on `PORT` for Railway readiness, without requiring
a public domain. Readiness requires a live child and a successful cycle from
that same process generation, no older than 180 seconds. The state also records
`RAILWAY_GIT_COMMIT_SHA`; an old certificate or a core-only success cannot pass.

Every 60 seconds the guard checks again. After a 180-second startup allowance,
three consecutive unhealthy probes restart the child process group. A child
exit also triggers repair. Repairs are capped at three per rolling hour per
guard process, with a ten-second backoff. Exhaustion exits nonzero; configure
Railway `ON_FAILURE` with at most three container retries. SIGTERM stops the
child and its subprocesses cleanly. No GitHub or Railway write credential is
needed, and health checks never rebuild or redeploy the application.

Enable Railway **Wait for CI** for the connected `main` branch. Changes to the
watched source paths deploy after push checks pass. Certificate-only commits
remain outside the watch paths. Platform deployment status and runtime guard
health remain separate from the mathematical core's certificate.
