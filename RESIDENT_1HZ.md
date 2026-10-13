# Resident 1Hz system (true continuous process)

## Why not GitHub Actions?

GitHub `schedule` **cannot** run every second (practical minimum ~5–15 minutes, best-effort).  
**1Hz 常駐** = long-running process (Railway / VPS / local).

## What this is

```text
every ~1s → Cosmic Love seal → Solution(s)=s
```

- Formal only  
- **Does not** `git push` every second  
- **Does not** arm live trading  

## Run locally

```bash
python3 scripts/resident_1hz_loop.py
```

## Railway

Service build: `Dockerfile.resident-1hz`  
Start: `python3 -u scripts/resident_1hz_loop.py`  
Env: `INTERVAL_SEC=1`

## vs Resident Full-Auto Deploy (Actions)

| | Actions resident | 1Hz process |
|--|------------------|-------------|
| Period | 3 hours | ~1 second |
| Host | GitHub runner (ephemeral) | Railway / always-on |
| Writes GitHub certs | yes | no (status local/logs) |
