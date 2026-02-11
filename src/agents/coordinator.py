from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from datetime import timezone
import inspect
from typing import Any
from typing import Callable
from typing import Mapping

from agents.cost_analyst import CostAnalystAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.history_agent import HistoryAgent
from agents.remediation_agent import RemediationAgent
from agents.resource_agent import ResourceAgent
from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.findings import InvestigationFindings
from models.findings import InvestigationReport
from models.findings import UnifiedFindings


class CoordinatorAgent:
    def __init__(
        self,
        *,
        cost_analyst: CostAnalystAgent | None = None,
        resource_agent: ResourceAgent | None = None,
        history_agent: HistoryAgent | None = None,
        diagnosis_agent: DiagnosisAgent | None = None,
        remediation_agent: RemediationAgent | None = None,
        per_agent_timeout_seconds: float = 20.0,
    ) -> None:
        self.cost_analyst = cost_analyst or CostAnalystAgent()
        self.resource_agent = resource_agent or ResourceAgent()
        self.history_agent = history_agent or HistoryAgent()
        self.diagnosis_agent = diagnosis_agent or DiagnosisAgent()
        self.remediation_agent = remediation_agent or RemediationAgent()
        self.per_agent_timeout_seconds = per_agent_timeout_seconds
        self.last_alert_id: str | None = None
        self.last_received_at: datetime | None = None
        self.alert_history: dict[str, datetime] = {}

    def handle_alert(self, alert_payload: Mapping[str, Any]) -> InvestigationReport:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.handle_alert_async(alert_payload))

        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(
                lambda: asyncio.run(self.handle_alert_async(alert_payload))
            ).result()

    async def handle_alert_async(
        self, alert_payload: Mapping[str, Any]
    ) -> InvestigationReport:
        received_at = datetime.now(timezone.utc)
        alert_id = self._extract_alert_id(alert_payload)
        alert_summary = self._build_alert_summary(alert_payload, alert_id, received_at)

        investigator_results = await asyncio.gather(
            self._run_agent_with_timeout(
                agent=AgentName.COST,
                runner=self.cost_analyst.run,
                payload=alert_payload,
                hints=None,
            ),
            self._run_agent_with_timeout(
                agent=AgentName.RESOURCE,
                runner=self.resource_agent.run,
                payload=alert_payload,
                hints=None,
            ),
            self._run_agent_with_timeout(
                agent=AgentName.HISTORY,
                runner=self.history_agent.run,
                payload=alert_payload,
                hints={"alert_summary": alert_summary},
            ),
        )
        results: list[AgentResult[Any]] = [*investigator_results]

        findings = UnifiedFindings.merge(results, alert_summary=alert_summary)
        diagnosis_result = await self._run_agent_with_timeout(
            agent=AgentName.DIAGNOSIS,
            runner=self.diagnosis_agent.run,
            payload=findings,
            hints=None,
        )
        remediation_result = await self._run_agent_with_timeout(
            agent=AgentName.REMEDIATION,
            runner=self.remediation_agent.run,
            payload=findings,
            hints=diagnosis_result.data,
        )

        self.last_alert_id = alert_id
        self.last_received_at = received_at
        self.alert_history[alert_id] = received_at

        return InvestigationReport(
            unified_findings=findings,
            diagnosis_result=diagnosis_result,
            remediation_result=remediation_result,
        )

    async def _run_agent_with_timeout(
        self,
        *,
        agent: AgentName,
        runner: Callable[..., Any],
        payload: Any,
        hints: Any,
    ) -> AgentResult[Any]:
        started_at = datetime.now(timezone.utc)
        try:
            raw_result = await asyncio.wait_for(
                asyncio.to_thread(self._invoke_runner, runner, payload, hints),
                timeout=self.per_agent_timeout_seconds,
            )
            return self._coerce_result(agent, raw_result, started_at)
        except asyncio.TimeoutError:
            return self._error_result(
                agent=agent,
                started_at=started_at,
                message=(
                    f"{agent.value} agent timed out after "
                    f"{self.per_agent_timeout_seconds:.0f}s"
                ),
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            return self._error_result(
                agent=agent,
                started_at=started_at,
                message=f"{agent.value} agent failed: {exc}",
            )

    def _invoke_runner(
        self,
        runner: Callable[..., Any],
        payload: Any,
        hints: Any,
    ) -> Any:
        parameters = inspect.signature(runner).parameters
        if len(parameters) >= 2:
            return runner(payload, hints)
        return runner(payload)

    def _coerce_result(
        self,
        expected_agent: AgentName,
        raw_result: Any,
        started_at: datetime,
    ) -> AgentResult[Any]:
        if isinstance(raw_result, AgentResult):
            if raw_result.agent == expected_agent:
                return raw_result

            return self._error_result(
                agent=expected_agent,
                started_at=started_at,
                message=(
                    f"{expected_agent.value} agent returned unexpected "
                    f"agent id {raw_result.agent.value}"
                ),
            )

        if expected_agent == AgentName.COST and isinstance(
            raw_result, InvestigationFindings
        ):
            note = raw_result.notes.strip()
            errors = [note] if note else []
            status = AgentStatus.DEGRADED if errors else AgentStatus.OK
            return AgentResult[InvestigationFindings](
                agent=AgentName.COST,
                status=status,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                data=raw_result,
                errors=errors,
            )

        return self._error_result(
            agent=expected_agent,
            started_at=started_at,
            message=(
                f"{expected_agent.value} agent returned unsupported result type "
                f"{type(raw_result).__name__}"
            ),
        )

    def _error_result(
        self,
        *,
        agent: AgentName,
        started_at: datetime,
        message: str,
    ) -> AgentResult[Any]:
        return AgentResult[Any](
            agent=agent,
            status=AgentStatus.ERROR,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            data=None,
            errors=[message],
        )

    def _build_alert_summary(
        self,
        alert_payload: Mapping[str, Any],
        alert_id: str,
        received_at: datetime,
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "alert_id": alert_id,
            "received_at": received_at,
        }
        for key in (
            "summary",
            "title",
            "resource_id",
            "resource_name",
            "resource_type",
            "anomaly_type",
        ):
            value = alert_payload.get(key)
            if value is not None:
                summary[key] = value
        return summary

    @staticmethod
    def _extract_alert_id(alert_payload: Mapping[str, Any]) -> str:
        alert_id = alert_payload.get("alert_id") or alert_payload.get("id")
        if alert_id is None:
            return "unknown-alert"
        return str(alert_id)
