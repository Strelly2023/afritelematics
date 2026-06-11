"""Shared runtime authority metadata for replay-backed proof surfaces."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


DOC_VERSION = "1.0.0"
VERIFIER_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "afritech/governance/document_registry.yaml"
SNAPSHOT_DIR = ROOT / "afritech/governance/authority_snapshots"


class AuthorityRuntimeError(RuntimeError):
    """Raised when runtime authority metadata drifts from governed doctrine."""


@lru_cache(maxsize=1)
def _registry_payload() -> dict[str, Any]:
    payload = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AuthorityRuntimeError("document registry payload must be a mapping")
    return payload


def _registry_document(doc_id: str) -> dict[str, Any]:
    payload = _registry_payload()
    for entry in payload.get("documents", ()):
        if isinstance(entry, dict) and entry.get("id") == doc_id:
            return entry
    raise AuthorityRuntimeError(f"unknown authority document: {doc_id}")


def _protocol_compatibility_payload() -> dict[str, Any]:
    payload = _registry_payload().get("protocol_compatibility")
    if not isinstance(payload, dict):
        raise AuthorityRuntimeError("protocol compatibility block missing")
    return payload


def _version_entries() -> tuple[dict[str, Any], ...]:
    entries = _protocol_compatibility_payload().get("versions")
    if not isinstance(entries, list) or not entries:
        raise AuthorityRuntimeError("protocol compatibility versions missing")
    normalized = tuple(entry for entry in entries if isinstance(entry, dict))
    if len(normalized) != len(entries):
        raise AuthorityRuntimeError("protocol compatibility entries must be mappings")
    return normalized


def _version_entry(version: str) -> dict[str, Any]:
    for entry in _version_entries():
        if str(entry.get("version")) == version:
            return entry
    raise AuthorityRuntimeError(f"unsupported protocol version: {version}")


def _parse_semver(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise AuthorityRuntimeError(f"invalid semantic version: {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def _pattern_matches(version: str, pattern: str) -> bool:
    subject_major, subject_minor, subject_patch = _parse_semver(version)
    target_major, target_minor, target_patch = pattern.split(".")
    if int(target_major) != subject_major or int(target_minor) != subject_minor:
        return False
    return target_patch == "x" or int(target_patch) == subject_patch


def compatibility_report(
    *,
    protocol_version: str,
    verifier_version: str = VERIFIER_VERSION,
) -> dict[str, Any]:
    compatibility = _protocol_compatibility_payload()
    entry = _version_entry(protocol_version)
    compatible_with = tuple(str(item) for item in entry.get("compatible_with", ()))
    supported = any(_pattern_matches(verifier_version, pattern) for pattern in compatible_with)
    return {
        "protocol_version": protocol_version,
        "verifier_version": verifier_version,
        "registry_current_version": str(compatibility.get("current_version", "")),
        "status": str(entry.get("status", "")),
        "breaking": bool(entry.get("breaking", False)),
        "compatible_with": list(compatible_with),
        "supported": supported,
    }


def assert_protocol_version_compatible(
    *,
    protocol_version: str,
    verifier_version: str = VERIFIER_VERSION,
) -> dict[str, Any]:
    report = compatibility_report(
        protocol_version=protocol_version,
        verifier_version=verifier_version,
    )
    if not report["supported"]:
        raise AuthorityRuntimeError(
            "protocol version incompatible with verifier: "
            f"protocol={protocol_version} verifier={verifier_version}"
        )
    return report


def validate_authority_binding(
    *,
    doc_id: str,
    doc_version: str,
    governed_invariants: tuple[str, ...],
) -> None:
    payload = _registry_payload()
    registry_version = str(payload.get("version", ""))
    if registry_version != doc_version:
        raise AuthorityRuntimeError(
            f"authority version mismatch: registry={registry_version} runtime={doc_version}"
        )
    assert_protocol_version_compatible(
        protocol_version=doc_version,
        verifier_version=VERIFIER_VERSION,
    )
    document = _registry_document(doc_id)
    binds = document.get("binds", {})
    declared_invariants = tuple(binds.get("invariants", ())) if isinstance(binds, dict) else ()
    if declared_invariants != governed_invariants:
        raise AuthorityRuntimeError(
            f"authority invariant mismatch: declared={declared_invariants} runtime={governed_invariants}"
        )


def authority_hash(
    *,
    doc_id: str,
    doc_version: str,
    governed_invariants: tuple[str, ...],
) -> str:
    encoded = json.dumps(
        {
            "doc_id": doc_id,
            "doc_version": doc_version,
            "governed_invariants": list(governed_invariants),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def authority_snapshot_payload(
    *,
    doc_id: str,
    doc_version: str,
    governed_invariants: tuple[str, ...],
) -> dict[str, Any]:
    document = _registry_document(doc_id)
    return {
        "schema": "afritech.authority_snapshot.v1",
        "authority_hash": authority_hash(
            doc_id=doc_id,
            doc_version=doc_version,
            governed_invariants=governed_invariants,
        ),
        "doc_id": doc_id,
        "doc_version": doc_version,
        "governed_invariants": list(governed_invariants),
        "bindings": document.get("binds", {}),
        "path": document.get("path"),
        "protocol_compatibility": compatibility_report(
            protocol_version=doc_version,
            verifier_version=VERIFIER_VERSION,
        ),
    }


def load_authority_snapshot(authority_digest: str) -> dict[str, Any]:
    path = SNAPSHOT_DIR / f"{authority_digest}.json"
    if not path.exists():
        raise AuthorityRuntimeError(f"missing authority snapshot: {authority_digest}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AuthorityRuntimeError("authority snapshot must be a mapping")
    if payload.get("authority_hash") != authority_digest:
        raise AuthorityRuntimeError("authority snapshot hash mismatch")
    return payload


def assert_consistent_authority_hashes(**named_hashes: str) -> str:
    present = {name: value for name, value in named_hashes.items() if value}
    unique = {value for value in present.values()}
    if len(unique) > 1:
        raise AuthorityRuntimeError(
            "authority hash mismatch: "
            + ", ".join(f"{name}={value}" for name, value in sorted(present.items()))
        )
    return next(iter(unique), "")


def execution_fingerprint(*, replay_hash: str, receipt_hash: str, authority_hash: str) -> str:
    encoded = json.dumps(
        {
            "replay_hash": replay_hash,
            "receipt_hash": receipt_hash,
            "authority_hash": authority_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def authority_envelope(
    *,
    doc_id: str,
    doc_version: str,
    governed_invariants: tuple[str, ...],
    surface: str,
) -> dict[str, Any]:
    validate_authority_binding(
        doc_id=doc_id,
        doc_version=doc_version,
        governed_invariants=governed_invariants,
    )
    digest = authority_hash(
        doc_id=doc_id,
        doc_version=doc_version,
        governed_invariants=governed_invariants,
    )
    load_authority_snapshot(digest)
    return {
        "doc_id": doc_id,
        "doc_version": doc_version,
        "governed_invariants": list(governed_invariants),
        "authority_hash": digest,
        "surface": surface,
    }
