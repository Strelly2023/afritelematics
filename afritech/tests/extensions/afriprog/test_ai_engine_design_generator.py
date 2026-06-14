from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.extensions.afriprog.ai_engine.design_generator import (
    DesignGenerator,
    StructuredDesignGeneratorError,
    StructuredDesignOutput,
)


class _FakeProposal:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def canonical_dict(self) -> dict[str, object]:
        return deepcopy(self._payload)


class _FakeOrchestrator:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls: list[str] = []

    def generate(self, intent: str) -> _FakeProposal:
        self.calls.append(intent)
        payload = deepcopy(self.payload)
        payload["intent"] = intent
        return _FakeProposal(payload)


class _FakeValidationResult:
    def __init__(self, admitted: bool, violations: tuple[str, ...] = ()) -> None:
        self.admitted = admitted
        self.violations = violations


class _RecordingValidator:
    def __init__(self, admitted: bool = True, violations: tuple[str, ...] = ()) -> None:
        self.admitted = admitted
        self.violations = violations
        self.seen: list[object] = []

    def validate(self, output: object) -> _FakeValidationResult:
        self.seen.append(output)
        return _FakeValidationResult(self.admitted, self.violations)


def _design_payload() -> dict[str, object]:
    return {
        "intent": "Build AfriPay",
        "domain": {"domain": "payments", "intent": "Build AfriPay"},
        "requirements": {"functional": ["ledger"], "non_functional": ["replay-safe"]},
        "architecture": {"modules": {"core": "afripay"}, "authority_boundary": "proposal_only"},
        "database": {"schema": "payments_core", "tables": ["transactions"]},
        "api": {"endpoints": ["/v1/payments"]},
        "events": {"topics": ["payment.completed"]},
        "implementation_plan": {"tasks": [{"task_id": "TASK-0001", "title": "Build core"}]},
        "evidence": {"evidence_id": "EVID-001", "source": "orchestrator"},
        "review": {"admitted": True, "violations": []},
        "write_enabled": False,
        "authority": "proposal_only",
    }


def test_structured_design_output_canonical_dict_is_locked_down():
    output = StructuredDesignOutput(
        intent="Build AfriPay",
        domain={"domain": "payments"},
        requirements={"functional": ["ledger"]},
        architecture={"modules": {"core": "afripay"}},
        contracts={"database": {"schema": "payments_core"}, "api": {}, "events": {}},
        implementation_plan={"tasks": [{"task_id": "TASK-0001"}]},
        evidence={"evidence_id": "EVID-001"},
        review={"admitted": True},
    )

    data = output.canonical_dict()

    assert data["schema"] == "afriprog.design_output.v1"
    assert data["format"] == "structured"
    assert data["authority"] == "proposal_only"
    assert data["write_enabled"] is False
    assert "text" not in data
    assert "markdown" not in data
    assert "body" not in data


def test_generate_happy_path_emits_structured_contracts():
    orchestrator = _FakeOrchestrator(_design_payload())
    validator = _RecordingValidator(admitted=True)
    generator = DesignGenerator(orchestrator=orchestrator, validator=validator)

    output = generator.generate("Build a Poultry Management System")
    data = output.canonical_dict()

    assert orchestrator.calls == ["Build a Poultry Management System"]
    assert len(validator.seen) == 1
    assert data["schema"] == "afriprog.design_output.v1"
    assert data["format"] == "structured"
    assert data["authority"] == "proposal_only"
    assert data["write_enabled"] is False
    assert sorted(data["contracts"]) == ["api", "database", "events"]
    assert data["contracts"]["database"]["schema"] == "payments_core"
    assert data["contracts"]["api"]["endpoints"] == ["/v1/payments"]
    assert data["contracts"]["events"]["topics"] == ["payment.completed"]
    assert data["review"]["admitted"] is True


def test_generate_rejects_invalid_intent():
    generator = DesignGenerator(
        orchestrator=_FakeOrchestrator(_design_payload()),
        validator=_RecordingValidator(admitted=True),
    )

    with pytest.raises(StructuredDesignGeneratorError):
        generator.generate("")

    with pytest.raises(StructuredDesignGeneratorError):
        generator.generate("   ")

    with pytest.raises(StructuredDesignGeneratorError):
        generator.generate(None)  # type: ignore[arg-type]


def test_generate_is_deterministic_for_same_intent():
    generator = DesignGenerator(
        orchestrator=_FakeOrchestrator(_design_payload()),
        validator=_RecordingValidator(admitted=True),
    )

    first = generator.generate("Build AfriPay").canonical_dict()
    second = generator.generate("Build AfriPay").canonical_dict()

    assert first == second


def test_generate_replay_stability_serialization_round_trip():
    generator = DesignGenerator(
        orchestrator=_FakeOrchestrator(_design_payload()),
        validator=_RecordingValidator(admitted=True),
    )

    result = generator.generate("Build AfriPay")
    encoded = json.dumps(result.canonical_dict(), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded == result.canonical_dict()


def test_generate_tampering_changes_canonical_output():
    generator = DesignGenerator(
        orchestrator=_FakeOrchestrator(_design_payload()),
        validator=_RecordingValidator(admitted=True),
    )

    result = generator.generate("Build AfriPay")
    tampered = deepcopy(result.canonical_dict())
    tampered["authority"] = "self_authorized"

    assert tampered != result.canonical_dict()


def test_generate_validation_failure_raises_structured_error():
    generator = DesignGenerator(
        orchestrator=_FakeOrchestrator(_design_payload()),
        validator=_RecordingValidator(admitted=False, violations=("authority must equal proposal_only",)),
    )

    with pytest.raises(StructuredDesignGeneratorError) as exc:
        generator.generate("Build AfriPay")

    assert "structured design output failed validation" in str(exc.value)
    assert "authority must equal proposal_only" in str(exc.value)


def test_generate_contracts_are_structured_and_no_free_text_surfaces():
    generator = DesignGenerator(
        orchestrator=_FakeOrchestrator(_design_payload()),
        validator=_RecordingValidator(admitted=True),
    )

    data = generator.generate("Build AfriPay").canonical_dict()

    assert {"text", "free_text", "markdown", "body", "content"}.isdisjoint(data)
    assert isinstance(data["domain"], dict)
    assert isinstance(data["requirements"], dict)
    assert isinstance(data["architecture"], dict)
    assert isinstance(data["contracts"], dict)
    assert isinstance(data["implementation_plan"], dict)
    assert isinstance(data["evidence"], dict)
    assert isinstance(data["review"], dict)

