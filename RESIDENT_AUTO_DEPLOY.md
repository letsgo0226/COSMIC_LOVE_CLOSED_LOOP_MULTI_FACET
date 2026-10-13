# Resident full-auto formal deployment system

## Goal

A **standing loop** that repeatedly re-deploys formal Cosmic Love certificates across all dimensions and facets:

```text
schedule / push → resident_auto_deploy_loop.py
  → stage scripts (closed-loop, HW-VM, account TM, …)
  → meta Solution(s)=s seals
  → certificates/LATEST_RESIDENT_AUTO_DEPLOY.json
  → commit [skip ci]
```

## Engine

Original Cosmic Love program only → **Solution(s)=s**.

## Resident trigger

Workflow `resident-auto-deploy.yml`:

- every **3 hours**
- on push to `main`
- manual `workflow_dispatch`

## Bound

Formal automation only. No live trading arm.
