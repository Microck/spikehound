from __future__ import annotations

import logging
from typing import Any

from fastapi import Body
from fastapi import FastAPI

from agents.coordinator import CoordinatorAgent
from web.settings import get_settings


settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("incident-war-room")

app = FastAPI(title="Incident War Room")
coordinator_agent = CoordinatorAgent()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/webhooks/alert")
async def webhook_alert(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    logger.info("webhook_received", extra={"payload": payload})
    findings = await coordinator_agent.handle_alert_async(payload)
    return findings.model_dump(mode="json")
