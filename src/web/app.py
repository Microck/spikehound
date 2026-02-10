from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from web.settings import get_settings


settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("incident-war-room")

app = FastAPI(title="Incident War Room")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "incident-war-room"}


@app.post("/webhooks/alert")
async def webhook_alert(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("webhook_received", extra={"payload": payload})
    return {"received": True}
