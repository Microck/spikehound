# Phase 4: User Setup Required

**Generated:** 2026-02-11
**Phase:** 04-human-loop
**Status:** Incomplete

Complete these items for Slack notification delivery, interactive approval buttons, and Azure remediation execution. Claude implemented the sender/execution wiring; these steps require Slack and Azure access.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `SLACK_WEBHOOK_URL` | Slack App -> Incoming Webhooks -> Copy Webhook URL | `.env` |
| [ ] | `SLACK_SIGNING_SECRET` | Slack App -> Basic Information -> App Credentials -> Signing Secret | `.env` |
| [ ] | `SLACK_BOT_TOKEN` | Slack App -> OAuth & Permissions -> Bot User OAuth Token | `.env` |
| [ ] | `AZURE_SUBSCRIPTION_ID` | Azure Portal -> Subscriptions -> Copy subscription ID | `.env` |

## Account Setup

- [ ] **Create or open a Slack app for TriageForge**
  - URL: https://api.slack.com/apps
  - Skip if: You already have an app used for this incident channel

- [ ] **Confirm Azure principal used by the app**
  - Location: Azure Portal -> Microsoft Entra ID -> Enterprise applications (or App registrations)
  - Notes: Use the same principal configured for your local credential flow/service principal

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

- [ ] **Grant remediation principal access to target resource group (demo scope)**
  - Location: Azure Portal -> Resource Group -> Access control (IAM)
  - Role: Contributor
  - Notes: Required for stop VM and auto-shutdown remediation calls

## Verification

After completing setup, verify with:

```bash
grep -E "SLACK_WEBHOOK_URL|SLACK_SIGNING_SECRET|SLACK_BOT_TOKEN|AZURE_SUBSCRIPTION_ID" .env
. .venv/bin/activate && PYTHONPATH=src python3 -c "from integrations.slack import send_webhook; send_webhook('TriageForge Slack setup verification')"
. .venv/bin/activate && PYTHONPATH=src python3 -c "from execution.remediation import execute_remediation; print('remediation module import ok')"
```

Expected results:
- All `SLACK_*` values and `AZURE_SUBSCRIPTION_ID` are present in `.env`
- Slack channel receives the verification message
- Slack button clicks are delivered to `/webhooks/slack/actions` once app interactivity is enabled
- Remediation executor import succeeds locally (Azure credentials still required at runtime)

---

**Once all items complete:** Mark status as "Complete" at top of file.
