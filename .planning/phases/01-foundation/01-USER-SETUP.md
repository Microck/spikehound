# Phase 01: User Setup Required

**Generated:** 2026-02-11
**Phase:** 01-foundation
**Status:** Incomplete

Complete these items for the Foundry integration to function. Claude automated everything possible; these items require human access to Azure AI Foundry / AI Studio.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `AZURE_AI_PROJECT_ENDPOINT` | Azure AI Foundry / AI Studio -> Project settings -> Endpoint (format: `https://{ai-services-account}.services.ai.azure.com/api/projects/{project-name}` or `/api/projects/_project`) | `.env` |

## Dashboard Configuration

- [ ] **Create or identify the Foundry project endpoint**
  - Location: Azure AI Foundry / AI Studio
  - Notes: Copy the endpoint into `AZURE_AI_PROJECT_ENDPOINT`.

## Verification

After completing setup, verify with:

```bash
. .venv/bin/activate
PYTHONPATH=src python scripts/foundry_smoke.py
```

Expected results:
- The script completes without creating resources.
- Output includes `Foundry read-only smoke check passed`.

---

**Once all items complete:** Mark status as "Complete" at top of file.
