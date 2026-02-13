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
from integrations.discord import parse_discord_custom_id
from integrations.discord import send_discord_webhook
from integrations.discord import verify_discord_signature
from integrations.message_format import format_investigation_report_for_discord
from integrations.message_format import format_investigation_report_for_slack
from integrations.slack import format_execution_outcomes_for_slack
from integrations.slack import send_webhook
from integrations.slack import verify_signature
from models.approval import ApprovalDecision
from models.approval import ApprovalRecord
from models.approval import ApprovalStore
from models.agent_protocol import AgentResult
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
processed_investigations: dict[str, tuple[float, InvestigationReport]] = {}

TRANSIENT_ERROR_MARKERS = (
    "timeout",
    "timed out",
    "network",
    "connection",
    "temporarily unavailable",
    "temporary failure",
    "reset by peer",
)

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
    investigation_id = str(normalized_payload["alert_id"])
    logger.info(
        "webhook_received",
        extra={"payload": payload, "normalized_payload": normalized_payload},
    )

    now_epoch = datetime.now(timezone.utc).timestamp()
    _prune_expired_processed_investigations(now_epoch)
    cached_report = _get_cached_report(investigation_id, now_epoch)
    if cached_report is not None:
        logger.info(
            "webhook_duplicate_returning_cached_report",
            extra={"investigation_id": investigation_id},
        )
        latest_reports[investigation_id] = cached_report
        if cached_report.remediation_result.data is not None:
            latest_remediation_plans[investigation_id] = (
                cached_report.remediation_result.data
            )
        return cached_report

    report = await _run_coordinator_with_retries(normalized_payload)
    latest_reports[investigation_id] = report
    if report.remediation_result.data is not None:
        latest_remediation_plans[investigation_id] = report.remediation_result.data
    else:
        latest_remediation_plans.pop(investigation_id, None)
    processed_investigations[investigation_id] = (now_epoch, report)

    try:
        slack_message = format_investigation_report_for_slack(report)
        send_webhook(
            slack_message["text"],
            blocks=slack_message.get("blocks"),
        )
    except Exception as exc:  # pragma: no cover - defensive protection
        logger.warning("slack_notification_failed", extra={"error": str(exc)})

    try:
        discord_message = format_investigation_report_for_discord(report)
        send_discord_webhook(discord_message)
    except Exception as exc:  # pragma: no cover - defensive protection
        logger.warning("discord_notification_failed", extra={"error": str(exc)})

    return report


async def _run_coordinator_with_retries(
    normalized_payload: Mapping[str, Any],
) -> InvestigationReport:
    report = await coordinator_agent.handle_alert_async(normalized_payload)
    for attempt in range(1, settings.max_agent_retries + 1):
        transient_messages = _transient_error_messages(report)
        if not transient_messages:
            break

        logger.warning(
            "retrying_after_transient_agent_errors",
            extra={
                "attempt": attempt,
                "max_retries": settings.max_agent_retries,
                "alert_id": normalized_payload.get("alert_id"),
                "errors": transient_messages,
            },
        )
        report = await coordinator_agent.handle_alert_async(normalized_payload)

    return report


def _transient_error_messages(report: InvestigationReport) -> list[str]:
    transient_errors: list[str] = []
    for result in _iter_agent_results(report):
        if result.status.value != "error":
            continue
        for error in result.errors:
            if _looks_transient_error(error):
                transient_errors.append(error)
    return transient_errors


def _iter_agent_results(report: InvestigationReport) -> list[AgentResult[Any]]:
    results = list(report.unified_findings.results.values())
    results.append(report.diagnosis_result)
    results.append(report.remediation_result)
    return results


def _looks_transient_error(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in TRANSIENT_ERROR_MARKERS)


def _get_cached_report(
    investigation_id: str,
    now_epoch: float,
) -> InvestigationReport | None:
    cached_entry = processed_investigations.get(investigation_id)
    if cached_entry is None:
        return None

    cached_at, cached_report = cached_entry
    if now_epoch - cached_at > settings.idempotency_ttl_seconds:
        processed_investigations.pop(investigation_id, None)
        return None
    return cached_report


def _prune_expired_processed_investigations(now_epoch: float) -> None:
    expiration_cutoff = now_epoch - settings.idempotency_ttl_seconds
    expired_investigations = [
        investigation_id
        for investigation_id, (cached_at, _) in processed_investigations.items()
        if cached_at < expiration_cutoff
    ]
    for investigation_id in expired_investigations:
        processed_investigations.pop(investigation_id, None)


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


@app.post("/webhooks/discord/interactions")
async def webhook_discord_interactions(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    raw_body = await request.body()
    if not verify_discord_signature(raw_body, request.headers):
        raise HTTPException(status_code=401, detail="invalid discord signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid discord payload") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid discord payload")

    interaction_type = payload.get("type")
    if interaction_type == 1:
        return {"type": 1}
    if interaction_type != 3:
        raise HTTPException(
            status_code=400,
            detail="unsupported discord interaction type",
        )

    custom_id = str(_as_mapping(payload.get("data")).get("custom_id") or "")
    parsed_custom_id = parse_discord_custom_id(custom_id)
    if parsed_custom_id is None:
        raise HTTPException(status_code=400, detail="invalid discord action")

    action_id, investigation_id = parsed_custom_id
    decision = ACTION_DECISION_MAP.get(action_id)
    if decision is None:
        raise HTTPException(status_code=400, detail="unsupported discord action")

    record = ApprovalRecord(
        investigation_id=investigation_id,
        decision=decision,
        decided_by=_extract_user_identifier(_extract_discord_user_payload(payload)),
        decided_at=datetime.now(timezone.utc),
        reason=(
            "Requested additional investigation"
            if decision is ApprovalDecision.INVESTIGATE
            else None
        ),
    )
    approval_records[investigation_id] = record
    logger.info(
        "discord_approval_recorded",
        extra={
            "investigation_id": investigation_id,
            "decision": decision.value,
            "decided_by": record.decided_by,
        },
    )

    response_text = f"Recorded **{decision.value}** decision for investigation `{investigation_id}`."
    if decision is ApprovalDecision.APPROVE:
        background_tasks.add_task(
            _execute_approved_remediation,
            investigation_id,
            record,
        )
        response_text = f"{response_text} Remediation execution has been queued."

    return {
        "type": 4,
        "data": {
            "content": response_text,
            "flags": 64,
        },
    }


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


def _extract_discord_user_payload(payload: Mapping[str, Any]) -> Any:
    member_payload = _as_mapping(payload.get("member"))
    member_user_payload = member_payload.get("user")
    if isinstance(member_user_payload, dict):
        return member_user_payload

    user_payload = payload.get("user")
    if isinstance(user_payload, dict):
        return user_payload

    return None
