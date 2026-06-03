"""Read-only execution explanation assembly."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


EXPLANATION_STATUS = "READ_ONLY_EXPLANATION"
RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False
VALIDATION_AUTHORITY = False
PROJECTION_DISPLAY_ONLY = True
AUTHORITY_BOUNDARY_STATEMENT = (
    "authority remains in governance YAML, validators, replay, and CI"
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXECUTION_REPORT_DIR = ROOT / "reports/executions"


@dataclass(frozen=True)
class ExecutionExplanation:
    """Read-only explanation payload for one execution artifact."""

    execution_id: str
    receipt: dict[str, Any]
    governance: list[dict[str, Any]]
    explanation: str
    authority: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "receipt": self.receipt,
            "governance": self.governance,
            "explanation": self.explanation,
            "authority": self.authority,
        }


class ExecutionExplanationStore:
    """Read-only JSON store for explanation inputs."""

    def __init__(self, report_dir: Path | str = DEFAULT_EXECUTION_REPORT_DIR) -> None:
        self.report_dir = Path(report_dir)

    def load(self, execution_id: str) -> dict[str, Any]:
        path = self._path(execution_id)
        if not path.exists():
            raise FileNotFoundError(execution_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("execution explanation artifact must be an object")
        return payload

    def _path(self, execution_id: str) -> Path:
        if not execution_id or execution_id in {".", ".."}:
            raise ValueError("invalid execution_id")
        if "/" in execution_id or "\\" in execution_id:
            raise ValueError("invalid execution_id")
        filename = execution_id if execution_id.endswith(".json") else f"{execution_id}.json"
        return self.report_dir / filename


def explain_execution_payload(
    execution_id: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Assemble a display-only explanation from receipt traceability metadata."""

    receipt = _receipt_from_payload(payload)
    references = _traceability_from_payload(payload, receipt)
    governance = _display_governance(references)
    explanation = ExecutionExplanation(
        execution_id=execution_id,
        receipt=receipt,
        governance=governance,
        explanation=_compose_explanation(execution_id, governance),
        authority=_authority_boundary(),
    )
    return explanation.as_dict()


def explain_execution_from_store(
    execution_id: str,
    store: ExecutionExplanationStore | None = None,
) -> dict[str, Any]:
    read_store = store or ExecutionExplanationStore()
    return explain_execution_payload(execution_id, read_store.load(execution_id))


def _receipt_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    receipt = payload.get("receipt", payload)
    if not isinstance(receipt, dict):
        raise ValueError("execution explanation requires a receipt object")
    return dict(receipt)


def _traceability_from_payload(
    payload: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> list[dict[str, str]]:
    traceability = payload.get("governance_traceability")
    if traceability is None:
        traceability = receipt.get("governance_traceability", ())
    if not isinstance(traceability, list):
        return []

    references: list[dict[str, str]] = []
    for item in traceability:
        if not isinstance(item, dict):
            continue
        ref_type = item.get("type")
        ref_id = item.get("id")
        if isinstance(ref_type, str) and isinstance(ref_id, str):
            references.append({"type": ref_type, "id": ref_id})
    return references


def _display_governance(references: list[dict[str, str]]) -> list[dict[str, Any]]:
    projection_index = _projection_display_index()
    governance: list[dict[str, Any]] = []
    for reference in references:
        ref_id = reference["id"]
        display = projection_index.get(ref_id, {})
        governance.append(
            {
                "type": reference["type"],
                "id": ref_id,
                "title": display.get("title", ""),
                "source_path": display.get("source_path", ""),
                "projection_status": display.get("projection_status", "DOCUMENTARY"),
                "display_only": True,
            }
        )
    return governance


def _projection_display_index() -> dict[str, dict[str, Any]]:
    from afritech.governance_projection.importer import project_governance

    bundle = project_governance()
    entries = (
        tuple(bundle.adrs)
        + tuple(bundle.invariants)
        + tuple(bundle.rules)
        + tuple(bundle.bindings)
        + tuple(bundle.ci_checks)
        + tuple(bundle.non_claims)
        + tuple(bundle.next_steps)
    )
    return {
        item.source_id: {
            "title": item.title,
            "source_path": item.source_path,
            "projection_status": item.projection_status,
        }
        for item in entries
    }


def _compose_explanation(execution_id: str, governance: list[dict[str, Any]]) -> str:
    if not governance:
        return (
            f"Execution {execution_id} has no governance references attached. "
            "This explanation is display-only and does not define runtime truth."
        )
    refs = ", ".join(item["id"] for item in governance)
    return (
        f"Execution {execution_id} references governance identifiers {refs}. "
        "These references explain traceability only; authority remains in "
        "governance YAML, validators, replay, and CI."
    )


def _authority_boundary() -> dict[str, Any]:
    return {
        "status": EXPLANATION_STATUS,
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "projection_display_only": PROJECTION_DISPLAY_ONLY,
    }
