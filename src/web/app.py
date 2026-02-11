from __future__ import annotations

import logging
from typing import Any

from fastapi import Body
from fastapi import FastAPI

from agents.coordinator import CoordinatorAgent
from integrations.message_format import format_investigation_report_for_slack
from integrations.slack import send_webhook
from models.findings import InvestigationReport
from web.settings import get_settings


settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("incident-war-room")

app = FastAPI(title="Incident War Room")
coordinator_agent = CoordinatorAgent()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/webhooks/alert", response_model=InvestigationReport)
async def webhook_alert(payload: dict[str, Any] = Body(...)) -> InvestigationReport:
    logger.info("webhook_received", extra={"payload": payload})
    report = await coordinator_agent.handle_alert_async(payload)

    try:
        slack_message = format_investigation_report_for_slack(report)
        send_webhook(
            slack_message["text"],
            blocks=slack_message.get("blocks"),
        )
    except Exception as exc:  # pragma: no cover - defensive protection
        logger.warning("slack_notification_failed", extra={"error": str(exc)})

    return report
