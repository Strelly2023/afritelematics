"""Deterministic logistics custody chain for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from ecosystems.afriride.geo.types import GeoPoint


SCHEMA = "afritech.mobility.logistics_custody_chain.v1"
AUTHORITY_BOUNDARY = "custody_chain_reference_only"
ALLOWED_ASSET_TYPES = ("person", "package", "food", "medicine", "document", "freight")
ALLOWED_CONDITIONS = ("sealed", "in_transit", "received", "handoff", "stored", "delivered")


class LogisticsCustodyError(ValueError):
    """Raised when a custody chain is invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LogisticsCustodyError(f"{label} is required")
    return value.strip()


def _geo_from_value(value: GeoPoint | Mapping[str, Any]) -> GeoPoint:
    if isinstance(value, GeoPoint):
        return value
    if not isinstance(value, Mapping):
        raise LogisticsCustodyError("location must be a mapping or GeoPoint")
    try:
        return GeoPoint(
            lat=float(value["lat"]),
            lon=float(value["lon"]),
            timestamp=int(value["timestamp"]),
        )
    except KeyError as exc:  # pragma: no cover - defensive
        raise LogisticsCustodyError(f"missing geo field: {exc.args[0]}") from exc


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _normalize_steps(values: Iterable[object]) -> tuple["CustodyStep", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise LogisticsCustodyError("custody_steps must be iterable")
    steps: list[CustodyStep] = []
    for item in values:
        if isinstance(item, CustodyStep):
            steps.append(item)
        elif isinstance(item, Mapping):
            steps.append(CustodyStep.from_mapping(item))
        else:
            raise LogisticsCustodyError("custody_steps must contain mappings or CustodyStep objects")
    if not steps:
        raise LogisticsCustodyError("at least one custody step is required")
    return tuple(steps)


@dataclass(frozen=True, order=True)
class CustodyStep:
    step_id: str
    from_participant: str | None
    to_participant: str
    location: GeoPoint
    timestamp: int
    condition: str
    evidence_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_id", _require_text(self.step_id, "step_id"))
        if self.from_participant is not None:
            object.__setattr__(self, "from_participant", _require_text(self.from_participant, "from_participant"))
        object.__setattr__(self, "to_participant", _require_text(self.to_participant, "to_participant"))
        object.__setattr__(self, "location", _geo_from_value(self.location))
        if not isinstance(self.timestamp, int):
            raise LogisticsCustodyError("timestamp must be an integer")
        if self.condition not in ALLOWED_CONDITIONS:
            raise LogisticsCustodyError(f"unsupported custody condition: {self.condition}")
        if not isinstance(self.evidence_hash, str) or len(self.evidence_hash) != 64:
            raise LogisticsCustodyError("evidence_hash must be a 64-character hex digest")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CustodyStep":
        if not isinstance(payload, Mapping):
            raise LogisticsCustodyError("custody step payload must be a mapping")
        return cls(
            step_id=_require_text(payload.get("step_id") or payload.get("id"), "step_id"),
            from_participant=payload.get("from_participant") or payload.get("from"),
            to_participant=_require_text(payload.get("to_participant") or payload.get("to"), "to_participant"),
            location=_geo_from_value(payload.get("location", {})),
            timestamp=int(payload.get("timestamp", 0)),
            condition=_require_text(payload.get("condition"), "condition"),
            evidence_hash=_require_text(payload.get("evidence_hash") or payload.get("hash"), "evidence_hash"),
        )

    @property
    def owner(self) -> str:
        return self.to_participant

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "evidence_hash": self.evidence_hash,
            "from_participant": self.from_participant,
            "location": self.location.canonical(),
            "owner": self.owner,
            "step_id": self.step_id,
            "timestamp": self.timestamp,
            "to_participant": self.to_participant,
        }

    def step_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class CustodyChain:
    chain_id: str
    operation_id: str
    asset_type: str
    custody_steps: tuple[CustodyStep, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "chain_id", _require_text(self.chain_id, "chain_id"))
        object.__setattr__(self, "operation_id", _require_text(self.operation_id, "operation_id"))
        if self.asset_type not in ALLOWED_ASSET_TYPES:
            raise LogisticsCustodyError(f"unsupported asset_type: {self.asset_type}")
        object.__setattr__(self, "custody_steps", _normalize_steps(self.custody_steps))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CustodyChain":
        if not isinstance(payload, Mapping):
            raise LogisticsCustodyError("custody chain payload must be a mapping")
        return cls(
            chain_id=_require_text(payload.get("chain_id") or payload.get("id"), "chain_id"),
            operation_id=_require_text(payload.get("operation_id"), "operation_id"),
            asset_type=_require_text(payload.get("asset_type"), "asset_type"),
            custody_steps=tuple(payload.get("custody_steps", ())),  # type: ignore[arg-type]
        )

    @property
    def step_count(self) -> int:
        return len(self.custody_steps)

    @property
    def participants(self) -> tuple[str, ...]:
        seen: list[str] = []
        for step in self.custody_steps:
            if step.from_participant and step.from_participant not in seen:
                seen.append(step.from_participant)
            if step.to_participant not in seen:
                seen.append(step.to_participant)
        return tuple(seen)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "asset_type": self.asset_type,
            "authority_boundary": self.authority_boundary,
            "chain_id": self.chain_id,
            "chain_hash": self.chain_hash,
            "custody_steps": [step.canonical_dict() for step in self.custody_steps],
            "operation_id": self.operation_id,
            "participants": list(self.participants),
            "schema": SCHEMA,
            "step_count": self.step_count,
        }

    @property
    def chain_hash(self) -> str:
        return _canonical_hash(
            {
                "asset_type": self.asset_type,
                "chain_id": self.chain_id,
                "custody_steps": [step.canonical_dict() for step in self.custody_steps],
                "operation_id": self.operation_id,
            }
        )

    @property
    def verified(self) -> bool:
        return True


@dataclass(frozen=True)
class CustodyValidationReport:
    chain_hash: str
    step_hashes: tuple[str, ...]
    verified: bool
    authority_boundary: str = AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "chain_hash": self.chain_hash,
            "schema": "afritech.mobility.custody_validation_report.v1",
            "step_hashes": list(self.step_hashes),
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate_custody_chain(chain: CustodyChain | Mapping[str, Any]) -> CustodyValidationReport:
    normalized = chain if isinstance(chain, CustodyChain) else CustodyChain.from_mapping(chain)
    checks = _validate_chain(normalized)
    if not checks["verified"]:
        raise LogisticsCustodyError(checks["reason"])
    return CustodyValidationReport(
        chain_hash=normalized.chain_hash,
        step_hashes=tuple(step.step_hash() for step in normalized.custody_steps),
        verified=True,
    )


def build_custody_chain_proof(chain: CustodyChain | Mapping[str, Any]) -> dict[str, Any]:
    normalized = chain if isinstance(chain, CustodyChain) else CustodyChain.from_mapping(chain)
    report = validate_custody_chain(normalized)
    proof = {
        "schema": "afritech.mobility.custody_chain_proof.v1",
        "authority_boundary": "custody_proof_read_only",
        "chain_id": normalized.chain_id,
        "chain_hash": normalized.chain_hash,
        "step_count": normalized.step_count,
        "participants": list(normalized.participants),
        "verified": report.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def export_custody_chain_proof(
    chain: CustodyChain | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    normalized = chain if isinstance(chain, CustodyChain) else CustodyChain.from_mapping(chain)
    proof = build_custody_chain_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "custody_chain.json"
    proof_path = target / "custody_proof.json"
    json_path.write_text(
        json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    proof_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": json_path, "proof": proof_path}


def _validate_chain(chain: CustodyChain) -> dict[str, Any]:
    seen_step_ids: set[str] = set()
    previous_timestamp: int | None = None
    previous_owner: str | None = None
    step_hashes: list[str] = []

    for index, step in enumerate(chain.custody_steps):
        if step.step_id in seen_step_ids:
            return {"verified": False, "reason": f"duplicate step_id: {step.step_id}"}
        seen_step_ids.add(step.step_id)
        if previous_timestamp is not None and step.timestamp < previous_timestamp:
            return {"verified": False, "reason": "custody steps must be timestamp ordered"}
        if index == 0 and step.from_participant is not None:
            return {"verified": False, "reason": "first step must start without a previous owner"}
        if index > 0 and step.from_participant != previous_owner:
            return {"verified": False, "reason": "custody continuity broken"}
        if index > 0 and step.from_participant is None:
            return {"verified": False, "reason": "handoff must be explicit"}
        previous_timestamp = step.timestamp
        previous_owner = step.to_participant
        step_hashes.append(step.step_hash())

    if len(chain.custody_steps) < 3:
        return {"verified": False, "reason": "custody chain must include explicit multi-hop handoff steps"}

    return {"verified": True, "reason": "ok", "step_hashes": step_hashes}


__all__ = [
    "ALLOWED_ASSET_TYPES",
    "ALLOWED_CONDITIONS",
    "AUTHORITY_BOUNDARY",
    "SCHEMA",
    "CustodyChain",
    "CustodyStep",
    "CustodyValidationReport",
    "LogisticsCustodyError",
    "build_custody_chain_proof",
    "export_custody_chain_proof",
    "validate_custody_chain",
]
