from __future__ import annotations

from datetime import datetime
from datetime import timezone
import json
import logging
from typing import Any
from typing import Mapping
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
    normalized_payload = normalize_alert_payload(payload)
    logger.info(
        "webhook_received",
        extra={"payload": payload, "normalized_payload": normalized_payload},
    )
    report = await coordinator_agent.handle_alert_async(normalized_payload)
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


def normalize_alert_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    root = dict(payload)
    data = _as_mapping(root.get("data"))
    essentials = _as_mapping(data.get("essentials"))
    alert_context = _as_mapping(data.get("alertContext"))

    alert_id = _first_non_empty_string(
        root.get("alert_id"),
        root.get("id"),
        essentials.get("alertId"),
        essentials.get("originAlertId"),
    )
    rule_name = _first_non_empty_string(
        root.get("rule_name"),
        root.get("ruleName"),
        essentials.get("alertRule"),
        root.get("summary"),
        root.get("title"),
    )
    severity = _first_non_empty_string(
        root.get("severity"),
        essentials.get("severity"),
        alert_context.get("severity"),
    )
    fired_date_time = _first_non_empty_string(
        root.get("fired_date_time"),
        root.get("firedDateTime"),
        essentials.get("firedDateTime"),
        root.get("timestamp"),
    )
    resource_id = _first_non_empty_string(
        root.get("resource_id"),
        root.get("resourceId"),
        _first_string_from_sequence(essentials.get("alertTargetIDs")),
        alert_context.get("resourceId"),
        _scan_resource_id(payload),
    )

    normalized: dict[str, Any] = {
        "alert_id": alert_id or "unknown-alert",
        "rule_name": rule_name or "unknown-rule",
        "severity": severity or "unknown",
        "fired_date_time": fired_date_time or datetime.now(timezone.utc).isoformat(),
        "summary": rule_name or "Alert received",
    }
    if resource_id is not None:
        normalized["resource_id"] = resource_id
    return normalized


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _first_non_empty_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _first_string_from_sequence(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    return stripped
    return None


def _scan_resource_id(payload: Any) -> str | None:
    candidates: list[str] = []
    _collect_resource_id_candidates(payload, candidates)
    return _first_non_empty_string(*candidates)


def _collect_resource_id_candidates(value: Any, candidates: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_name = str(key).lower()
            if key_name in {"resource_id", "resourceid", "resourceuri"} and isinstance(
                child, str
            ):
                candidates.append(child)
            elif key_name == "id" and isinstance(child, str):
                if child.lower().startswith("/subscriptions/"):
                    candidates.append(child)

            if isinstance(child, Mapping) or isinstance(child, list):
                _collect_resource_id_candidates(child, candidates)
        return

    if isinstance(value, list):
        for item in value:
            _collect_resource_id_candidates(item, candidates)


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
