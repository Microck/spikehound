from __future__ import annotations

from typing import Any
from typing import Mapping

from pydantic import BaseModel


def format_investigation_report_for_slack(report: Any) -> dict[str, Any]:
    payload = _to_mapping(report)
    unified_findings = _to_mapping(payload.get("unified_findings"))
    diagnosis_data = _to_mapping(
        _to_mapping(payload.get("diagnosis_result")).get("data")
    )
    diagnosis_hypothesis = _to_mapping(diagnosis_data.get("hypothesis"))
    remediation_data = _to_mapping(
        _to_mapping(payload.get("remediation_result")).get("data")
    )

    top_cost_drivers = _top_cost_drivers(unified_findings.get("cost_findings"))
    cost_driver_text = ", ".join(top_cost_drivers) if top_cost_drivers else "none"
    confidence = diagnosis_data.get("confidence")
    confidence_text = f"{confidence}%" if isinstance(confidence, int) else "unknown"
    root_cause_title = str(diagnosis_hypothesis.get("title") or "Unknown root cause")
    first_action = _first_remediation_action(remediation_data.get("actions"))
    alert_id = str(unified_findings.get("alert_id") or "unknown-alert")

    text = (
        f"Investigation complete for {alert_id}. "
        f"Top cost driver(s): {cost_driver_text}. "
        f"Confidence: {confidence_text}. "
        f"Root cause: {root_cause_title}. "
        f"First remediation action: {first_action}."
    )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Incident Investigation Complete",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Alert:* `{alert_id}`\n"
                    f"*Top cost driver(s):* {cost_driver_text}\n"
                    f"*Confidence:* {confidence_text}\n"
                    f"*Root cause:* {root_cause_title}\n"
                    f"*First remediation action:* {first_action}"
                ),
            },
        },
    ]

    return {"text": text, "blocks": blocks}


def _to_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _top_cost_drivers(cost_findings: Any) -> list[str]:
    if not isinstance(cost_findings, list):
        return []

    normalized: list[dict[str, Any]] = []
    for finding in cost_findings:
        mapping = _to_mapping(finding)
        cost = mapping.get("cost")
        if not isinstance(cost, (int, float)):
            continue
        normalized.append(
            {
                "resource_id": str(mapping.get("resource_id") or "unknown-resource"),
                "cost": float(cost),
                "currency": str(mapping.get("currency") or "USD"),
            }
        )

    normalized.sort(key=lambda item: item["cost"], reverse=True)
    top_drivers: list[str] = []
    for item in normalized[:3]:
        resource_label = _resource_label(item["resource_id"])
        top_drivers.append(f"{resource_label} (${item['cost']:.2f} {item['currency']})")
    return top_drivers


def _resource_label(resource_id: str) -> str:
    parts = [part for part in resource_id.split("/") if part]
    if parts:
        return parts[-1]
    return resource_id


def _first_remediation_action(actions: Any) -> str:
    if not isinstance(actions, list) or not actions:
        return "none"

    first_action = _to_mapping(actions[0])
    action_type = str(first_action.get("type") or "unknown_action")
    target_resource_id = str(first_action.get("target_resource_id") or "")
    target_label = (
        _resource_label(target_resource_id) if target_resource_id else "unknown"
    )
    return f"{action_type} on {target_label}"
