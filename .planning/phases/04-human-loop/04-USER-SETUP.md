# Phase 4: User Setup Required

**Generated:** 2026-02-11
**Phase:** 04-human-loop
**Status:** Incomplete

Complete these items for Slack notification delivery. Claude implemented the webhook sender and formatter; these steps require your Slack workspace access.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `SLACK_WEBHOOK_URL` | Slack Workspace -> Apps -> Incoming Webhooks -> Copy Webhook URL | `.env` |

## Account Setup

- [ ] **Create or open a Slack app with Incoming Webhooks enabled**
  - URL: https://api.slack.com/apps
  - Skip if: You already have an app configured for this project/channel

## Dashboard Configuration

- [ ] **Enable Incoming Webhooks**
  - Location: Slack App Configuration -> Features -> Incoming Webhooks
  - Set to: Enabled

- [ ] **Add webhook to the incident channel**
  - Location: Slack App Configuration -> Incoming Webhooks -> Add New Webhook to Workspace
  - Set to: Incident response channel used by your team
  - Notes: Copy the generated webhook URL into `SLACK_WEBHOOK_URL`

## Verification

After completing setup, verify with:

```bash
grep SLACK_WEBHOOK_URL .env
. .venv/bin/activate && PYTHONPATH=src python3 -c "from integrations.slack import send_webhook; send_webhook('TriageForge Slack setup verification')"
```

Expected results:
- `SLACK_WEBHOOK_URL` is present in `.env`
- Slack channel receives the verification message

---

**Once all items complete:** Mark status as "Complete" at top of file.
