from __future__ import annotations

from datetime import datetime
from datetime import timezone
import json
import logging
from typing import Any
from urllib.parse import parse_qs

from fastapi import BackgroundTasks
from fastapi import Body
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request

from agents.coordinator import CoordinatorAgent
from execution.remediation import execute_remediation
from integrations.message_format import format_investigation_report_for_slack
from integrations.slack import format_execution_outcomes_for_slack
from integrations.slack import send_webhook
from integrations.slack import verify_signature
from models.approval import ApprovalDecision
from models.approval import ApprovalRecord
from models.approval import ApprovalStore
from models.findings import InvestigationReport
from models.remediation import RemediationPlan
from web.settings import get_settings


settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("incident-war-room")

app = FastAPI(title="Incident War Room")
coordinator_agent = CoordinatorAgent()
approval_records: ApprovalStore = {}
latest_reports: dict[str, InvestigationReport] = {}
latest_remediation_plans: dict[str, RemediationPlan] = {}

ACTION_DECISION_MAP: dict[str, ApprovalDecision] = {
    "approve_remediation": ApprovalDecision.APPROVE,
    "reject_remediation": ApprovalDecision.REJECT,
    "investigate_more": ApprovalDecision.INVESTIGATE,
}


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/webhooks/alert", response_model=InvestigationReport)
async def webhook_alert(payload: dict[str, Any] = Body(...)) -> InvestigationReport:
    logger.info("webhook_received", extra={"payload": payload})
    report = await coordinator_agent.handle_alert_async(payload)
    investigation_id = report.unified_findings.alert_id
    latest_reports[investigation_id] = report
    if report.remediation_result.data is not None:
        latest_remediation_plans[investigation_id] = report.remediation_result.data
    else:
        latest_remediation_plans.pop(investigation_id, None)

    try:
        slack_message = format_investigation_report_for_slack(report)
        send_webhook(
            slack_message["text"],
            blocks=slack_message.get("blocks"),
        )
    except Exception as exc:  # pragma: no cover - defensive protection
        logger.warning("slack_notification_failed", extra={"error": str(exc)})

    return report


@app.post("/webhooks/slack/actions")
async def webhook_slack_actions(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    raw_body = await request.body()
    if not verify_signature(raw_body, request.headers):
        raise HTTPException(status_code=401, detail="invalid slack signature")

    form_data = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
    payload_raw = form_data.get("payload", [None])[0]
    if payload_raw is None:
        raise HTTPException(status_code=400, detail="missing slack payload")

    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid slack payload") from exc

    actions = payload.get("actions")
    if not isinstance(actions, list) or not actions:
        raise HTTPException(status_code=400, detail="missing slack action")

    action = actions[0]
    if not isinstance(action, dict):
        raise HTTPException(status_code=400, detail="invalid slack action")

    action_id = str(action.get("action_id") or "")
    decision = ACTION_DECISION_MAP.get(action_id)
    if decision is None:
        raise HTTPException(status_code=400, detail="unsupported slack action")

    investigation_id = str(action.get("value") or "")
    if not investigation_id:
        raise HTTPException(status_code=400, detail="missing investigation id")

    record = ApprovalRecord(
        investigation_id=investigation_id,
        decision=decision,
        decided_by=_extract_user_identifier(payload.get("user")),
        decided_at=datetime.now(timezone.utc),
        reason=(
            "Requested additional investigation"
            if decision is ApprovalDecision.INVESTIGATE
            else None
        ),
    )
    approval_records[investigation_id] = record
    logger.info(
        "slack_approval_recorded",
        extra={
            "investigation_id": investigation_id,
            "decision": decision.value,
            "decided_by": record.decided_by,
        },
    )

    response_text = (
        f"Recorded *{decision.value}* decision for investigation `{investigation_id}`."
    )
    if decision is ApprovalDecision.APPROVE:
        background_tasks.add_task(
            _execute_approved_remediation,
            investigation_id,
            record,
        )
        response_text = f"{response_text} Remediation execution has been queued."

    return {"text": response_text}


def _execute_approved_remediation(
    investigation_id: str,
    approval_record: ApprovalRecord,
) -> None:
    remediation_plan = latest_remediation_plans.get(investigation_id)
    if remediation_plan is None:
        logger.warning(
            "remediation_execution_skipped",
            extra={
                "investigation_id": investigation_id,
                "reason": "missing remediation plan",
            },
        )
        send_webhook(
            "Remediation approval received, but no remediation plan was found for "
            f"investigation `{investigation_id}`."
        )
        return

    outcomes = execute_remediation(remediation_plan, approval_record)
    follow_up = format_execution_outcomes_for_slack(investigation_id, outcomes)
    send_webhook(
        follow_up["text"],
        blocks=follow_up.get("blocks"),
    )


def _extract_user_identifier(user_payload: Any) -> str:
    if isinstance(user_payload, dict):
        for key in ("username", "name", "id"):
            value = user_payload.get(key)
            if isinstance(value, str) and value:
                return value
    return "unknown-user"
