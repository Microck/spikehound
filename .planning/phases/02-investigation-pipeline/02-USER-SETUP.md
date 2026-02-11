# Phase 02: User Setup Required

**Generated:** 2026-02-11
**Phase:** 02-investigation-pipeline
**Status:** Incomplete

Complete these items for the history incident backend integration to function. Claude automated everything possible; these items require human access to Azure dashboards and secrets.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `AZURE_SEARCH_ENDPOINT` | Azure Portal -> AI Search -> Overview -> URL | `.env` |
| [ ] | `AZURE_SEARCH_API_KEY` | Azure Portal -> AI Search -> Keys -> Admin key | `.env` |
| [ ] | `AZURE_SEARCH_INDEX` | Azure Portal -> AI Search -> Indexes -> Incident index name | `.env` |
| [ ] | `COSMOS_ENDPOINT` | Azure Portal -> Cosmos DB -> Overview -> URI | `.env` |
| [ ] | `COSMOS_KEY` | Azure Portal -> Cosmos DB -> Keys -> Primary key | `.env` |
| [ ] | `COSMOS_DATABASE` | Cosmos DB database name used for incidents | `.env` |
| [ ] | `COSMOS_CONTAINER` | Cosmos DB container name used for incidents | `.env` |

## Dashboard Configuration

- [ ] **Create or verify Cosmos DB database/container for incidents**
  - Location: Azure Portal -> Cosmos DB -> Data Explorer
  - Notes: In non-dev environments the app does not auto-create missing database/container resources.

- [ ] **Create or verify AI Search index for incidents**
  - Location: Azure Portal -> AI Search -> Indexes
  - Notes: Index should include an `id` key field and searchable incident text fields.

## Verification

After completing setup, verify with:

```bash
. .venv/bin/activate
PYTHONPATH=src pytest -q tests/test_history_agent_smoke.py
```

Expected results:
- Tests pass.
- `HistoryAgent` does not report missing Azure backend configuration variables.

---

**Once all items complete:** Mark status as "Complete" at top of file.
