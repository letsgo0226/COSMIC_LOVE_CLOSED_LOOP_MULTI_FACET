# Fix: Gmail failure storm (push race)

## Cause
Multiple workflows on `push` + simultaneous `git push` of certificates → non-fast-forward → Actions fail → email flood.

## Fix (2026-10-13)
- Removed `on: push` from certificate writers (schedule + workflow_dispatch only)
- Shared concurrency group `cosmic-love-certificates`
- Rebase-safe push with retries
- Staggered crons ( :00 / :10 / :20 / :40 / :50 )

Resident remains the main full loop every 3 hours.
