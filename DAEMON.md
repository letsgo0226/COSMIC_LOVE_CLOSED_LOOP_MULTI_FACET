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
