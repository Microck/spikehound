# Phase 5 Plan 05-04 Summary: Hardening Pass

## Status

**Status:** Completed ✅
**Date:** 2026-02-11

## Why This Plan Exists

After Phase 5 completion, we did an additional hardening pass to reduce demo-day risk:
- Fix Azure CLI power state retrieval in demo scripts
- Make diagram rendering resilient when Puppeteer/npx fails in headless environments
- Remove personal identifiers from demo docs
- Reconcile planning verification/state accuracy

## What Changed

### 1. Demo scripts hardened

Updated:
- `demo/stage_anomaly.sh`
- `demo/cleanup_demo.sh`

Key improvements:
- Strict bash mode (`set -euo pipefail`)
- `--help`/usage support and required-arg validation
- Validate `az` exists and Azure CLI is authenticated
- Retrieve power state using `az vm show -d --query powerState` (required for `powerState` to exist)
- Print commands before executing
- Use consistent tag keys (`demo`, `demo_scenario`, `demo_date`) for stage/cleanup symmetry

### 2. Diagram rendering made resilient

Updated:
- `docs/render_architecture.sh`

Key improvements:
- If `npx @mermaid-js/mermaid-cli` fails (Puppeteer chrome-headless-shell error), fallback automatically to Docker (`minlag/mermaid-cli`)
- Fail fast if output PNG is missing/empty

### 3. Demo docs scrubbed of personal identifiers

Updated:
- `demo/scenario.md`
- `demo/script.md`
- `demo/recording_checklist.md`

Key improvements:
- Removed hardcoded subscription ID and personal email; replaced with placeholders (`<your-subscription-id>`) or generic CLI queries

### 4. Planning docs reconciled

Updated:
- `.planning/phases/04-human-loop/04-human-loop-VERIFICATION.md`
- `.planning/phases/05-demo-submit/05-01-SUMMARY.md`
- `.planning/phases/05-demo-submit/05-demo-submit-VERIFICATION.md`
- `.planning/STATE.md`

Key improvements:
- Phase 4 verification now distinguishes local simulation vs environment-dependent validation
- Phase 5 verification re-verified after hardening
- STATE updated to reflect 05-04 completion and updated plan counts

## Verification

Verified locally:
- `bash -n demo/stage_anomaly.sh && bash -n demo/cleanup_demo.sh`
- `bash -n docs/render_architecture.sh && bash docs/render_architecture.sh && test -s docs/architecture.png`
- `python -m pytest tests/` (33 passed)
- `rg -n "marcos\.jaen\.lego@gmail\.com|495eb1d8-99ac-40d1-9eaf-082d28b8ac56" -S .` returns no matches

## Commits

- Plan: `991de3d` (docs)
- Execution (hardening): `fa8d322` (chore)

## Notes / Remaining Human Checks

- Real Slack UI button clicks still require exposing `/webhooks/slack/actions` via a public URL (ngrok/tunnel) and configuring Slack Interactivity.
- Real Azure side effects still require an end-to-end rehearsal on a safe test VM (run pipeline -> approve -> confirm powerState).

---

_Completed: 2026-02-11_
