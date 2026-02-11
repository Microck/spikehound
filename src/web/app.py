from __future__ import annotations

import logging
from typing import Any

from fastapi import Body
from fastapi import FastAPI

from web.settings import get_settings


settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("incident-war-room")

app = FastAPI(title="Incident War Room")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/webhooks/alert")
async def webhook_alert(payload: Any = Body(...)) -> dict[str, bool]:
    logger.info("webhook_received", extra={"payload": payload})
    return {"received": True}
