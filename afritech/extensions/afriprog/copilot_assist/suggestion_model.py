from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Final


SUGGESTION_SCHEMA: Final[str] = "afriprog.copilot_assist.suggestion.v1"
AUTHORITY: Final[str] = "developer_assistance_only"
ASSISTANCE_KINDS: Final[tuple[str, ...]] = (
    "inline_code_suggestion",
    "context_file_analysis",
    "explain_this_code",
    "generate_tests",
    "fix_failing_validator",
    "generate_contract_binding",
    "generate_replay_fixture",
    "suggest_refactor",
    "create_rollback_plan",
    "confidence_and_validators",
)
FINAL_AUTHORITIES: Final[tuple[str, ...]] = (
    "contracts",
    "validators",
    "replay",
    "governance",
)


@dataclass(frozen=True)
class CopilotSuggestion:
    suggestion_id: str
    kind: str
    intent: str
    target: str
    body: str
    confidence: float
    required_validators: tuple[str, ...]
    explanation: str
    authority: str = AUTHORITY
    schema: str = SUGGESTION_SCHEMA
    accepted: bool = False
    mutates_runtime: bool = False
    execution_authority: bool = False
    proof_authority: bool = False
    replay_authority: bool = False
    governance_authority: bool = False

    def canonical_dict(self) -> dict[str, object]:
        payload = {
            "schema": self.schema,
            "suggestion_id": self.suggestion_id,
            "kind": self.kind,
            "intent": self.intent,
            "target": self.target,
            "body": self.body,
            "confidence": self.confidence,
            "required_validators": self.required_validators,
            "explanation": self.explanation,
            "authority": self.authority,
            "accepted": self.accepted,
            "mutates_runtime": self.mutates_runtime,
            "execution_authority": self.execution_authority,
            "proof_authority": self.proof_authority,
            "replay_authority": self.replay_authority,
            "governance_authority": self.governance_authority,
            "final_authorities": FINAL_AUTHORITIES,
        }
        payload["suggestion_hash"] = suggestion_hash(payload)
        return payload


def suggestion_hash(payload: dict[str, object]) -> str:
    material = dict(payload)
    material.pop("suggestion_hash", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_suggestion_id(kind: str, intent: str, target: str) -> str:
    seed = {"kind": kind, "intent": intent, "target": target}
    return "afriprog-suggestion-" + suggestion_hash(seed)[:16]


__all__ = [
    "ASSISTANCE_KINDS",
    "AUTHORITY",
    "FINAL_AUTHORITIES",
    "SUGGESTION_SCHEMA",
    "CopilotSuggestion",
    "build_suggestion_id",
    "suggestion_hash",
]
