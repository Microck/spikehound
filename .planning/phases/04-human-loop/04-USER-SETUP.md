# Phase 4: User Setup Required

**Generated:** 2026-02-11
**Phase:** 04-human-loop
**Status:** Incomplete

Complete these items for Slack notification delivery and interactive approval buttons. Claude implemented the webhook sender, button formatting, and action endpoint; these steps require Slack workspace access.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `SLACK_WEBHOOK_URL` | Slack App -> Incoming Webhooks -> Copy Webhook URL | `.env` |
| [ ] | `SLACK_SIGNING_SECRET` | Slack App -> Basic Information -> App Credentials -> Signing Secret | `.env` |
| [ ] | `SLACK_BOT_TOKEN` | Slack App -> OAuth & Permissions -> Bot User OAuth Token | `.env` |

## Account Setup

- [ ] **Create or open a Slack app for TriageForge**
  - URL: https://api.slack.com/apps
  - Skip if: You already have an app used for this incident channel

## Dashboard Configuration

- [ ] **Enable Incoming Webhooks and add a channel webhook**
  - Location: Slack App -> Features -> Incoming Webhooks
  - Set to: Enabled, then Add New Webhook to Workspace
  - Notes: Copy generated webhook URL to `SLACK_WEBHOOK_URL`

- [ ] **Enable Interactivity & Shortcuts for button callbacks**
  - Location: Slack App -> Features -> Interactivity & Shortcuts
  - Request URL: `https://<your-public-domain>/webhooks/slack/actions`
  - Notes: Localhost will not receive Slack callbacks; use a reachable dev tunnel/domain

- [ ] **Install/Reinstall app to workspace after permission changes**
  - Location: Slack App -> OAuth & Permissions
  - Notes: Confirm bot token value used for `SLACK_BOT_TOKEN`

## Verification

After completing setup, verify with:

```bash
grep -E "SLACK_WEBHOOK_URL|SLACK_SIGNING_SECRET|SLACK_BOT_TOKEN" .env
. .venv/bin/activate && PYTHONPATH=src python3 -c "from integrations.slack import send_webhook; send_webhook('TriageForge Slack setup verification')"
```

Expected results:
- All three `SLACK_*` values are present in `.env`
- Slack channel receives the verification message
- Slack button clicks are delivered to `/webhooks/slack/actions` once app interactivity is enabled

---

**Once all items complete:** Mark status as "Complete" at top of file.
