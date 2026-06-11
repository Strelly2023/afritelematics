"""Guard the governed documentation authority registry."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "afritech/governance/document_registry.yaml"
INVARIANTS = ROOT / "afritech/constitution/INVARIANTS.yaml"
SWEEP_DOC = ROOT / "docs/reviews/AFRITECH_CANONICAL_CONFLICT_SWEEP.md"
SCAN_ROOTS = (ROOT / "docs", ROOT / "afritech")

AUTHORITY_PATTERNS = (
    re.compile(r"canonical documentation navigation surface", re.IGNORECASE),
    re.compile(r"documentation root index", re.IGNORECASE),
    re.compile(r"canonical specification artifact", re.IGNORECASE),
    re.compile(r"final canonical closure", re.IGNORECASE),
    re.compile(r"fully structured canonical specification", re.IGNORECASE),
)


class DocumentRegistryGuardError(RuntimeError):
    """Raised when documentation authority drifts."""


@dataclass(frozen=True)
class DocumentRegistryGuardReport:
    registry_path: str
    registry_version: str
    registered_document_count: int
    historical_conflict_count: int
    compatibility_entry_count: int
    root_navigation_doc: str
    constitutional_root_doc: str
    architecture_root_doc: str
    invariant_binding_count: int
    code_surface_binding_count: int
    unregistered_authority_claims: tuple[str, ...]
    unbound_registered_docs: tuple[str, ...]
    invalid_invariant_bindings: tuple[str, ...]
    invalid_code_surface_bindings: tuple[str, ...]
    module_metadata_mismatches: tuple[str, ...]
    module_version_mismatches: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not (
            self.unregistered_authority_claims
            or self.unbound_registered_docs
            or self.invalid_invariant_bindings
            or self.invalid_code_surface_bindings
            or self.module_metadata_mismatches
            or self.module_version_mismatches
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["clean"] = self.clean
        return payload


def validate() -> DocumentRegistryGuardReport:
    payload = _load_yaml(REGISTRY)
    invariant_payload = _load_yaml(INVARIANTS)
    if payload.get("schema") != "afritech.governance.document_registry.v1":
        raise DocumentRegistryGuardError("document registry schema mismatch")
    if payload.get("classification") != "DOCUMENT_AUTHORITY_REGISTRY":
        raise DocumentRegistryGuardError("document registry classification mismatch")
    registry_version = str(payload.get("version", ""))
    if not registry_version:
        raise DocumentRegistryGuardError("document registry version missing")
    known_invariants = {
        str(item["id"])
        for item in invariant_payload.get("invariants", ())
        if isinstance(item, dict) and "id" in item
    }
    compatibility_entries = _validate_protocol_compatibility(
        compatibility=payload.get("protocol_compatibility"),
        registry_version=registry_version,
    )

    documents = payload.get("documents")
    conflicts = payload.get("historical_conflicts")
    if not isinstance(documents, list) or not documents:
        raise DocumentRegistryGuardError("document registry must declare documents")
    if not isinstance(conflicts, list) or not conflicts:
        raise DocumentRegistryGuardError("document registry must declare historical conflicts")

    ids: set[str] = set()
    paths: set[str] = set()
    registered_paths: set[str] = set()
    invariant_binding_count = 0
    code_surface_binding_count = 0
    unbound_registered_docs: list[str] = []
    invalid_invariant_bindings: list[str] = []
    invalid_code_surface_bindings: list[str] = []
    module_metadata_mismatches: list[str] = []
    module_version_mismatches: list[str] = []
    code_surface_to_doc: dict[str, dict[str, Any]] = {}

    for entry in documents:
        if not isinstance(entry, dict):
            raise DocumentRegistryGuardError("document entry must be a mapping")
        doc_id = str(entry.get("id", ""))
        path = str(entry.get("path", ""))
        if not doc_id or not path:
            raise DocumentRegistryGuardError("document entry missing id or path")
        if doc_id in ids:
            raise DocumentRegistryGuardError(f"duplicate document id: {doc_id}")
        if path in paths:
            raise DocumentRegistryGuardError(f"duplicate document path: {path}")
        _require_exists(path)
        ids.add(doc_id)
        paths.add(path)
        registered_paths.add(path)
        binds = entry.get("binds")
        if entry.get("authority") not in {"ROOT_NAVIGATION", "GOVERNANCE_REVIEW"}:
            if not isinstance(binds, dict):
                unbound_registered_docs.append(doc_id)
                continue
            invariants = binds.get("invariants", ())
            code_surfaces = binds.get("code_surfaces", ())
            if not invariants and not code_surfaces:
                unbound_registered_docs.append(doc_id)
            if invariants:
                if not isinstance(invariants, list):
                    invalid_invariant_bindings.append(f"{doc_id}:invariants_not_list")
                else:
                    invariant_binding_count += len(invariants)
                    for invariant_id in invariants:
                        if invariant_id not in known_invariants:
                            invalid_invariant_bindings.append(f"{doc_id}:{invariant_id}")
            if code_surfaces:
                if not isinstance(code_surfaces, list):
                    invalid_code_surface_bindings.append(f"{doc_id}:code_surfaces_not_list")
                else:
                    code_surface_binding_count += len(code_surfaces)
                    for code_surface in code_surfaces:
                        _require_exists(code_surface)
                        if code_surface in code_surface_to_doc:
                            invalid_code_surface_bindings.append(
                                f"{code_surface}:duplicate_binding:{code_surface_to_doc[code_surface]['id']}:{doc_id}"
                            )
                        code_surface_to_doc[code_surface] = {
                            "id": doc_id,
                            "version": registry_version,
                            "invariants": tuple(invariants) if isinstance(invariants, list) else (),
                        }

    root_navigation = _require_single_document(documents, "ROOT_NAVIGATION")
    constitutional_root = _require_single_document(documents, "CONSTITUTIONAL_ROOT")
    architecture_root = _require_single_document(documents, "ARCHITECTURE_ROOT")

    historical_paths: set[str] = set()
    for entry in conflicts:
        if not isinstance(entry, dict):
            raise DocumentRegistryGuardError("historical conflict entry must be a mapping")
        path = str(entry.get("path", ""))
        disposition = str(entry.get("disposition", ""))
        if not path or not disposition:
            raise DocumentRegistryGuardError("historical conflict missing path or disposition")
        _require_exists(path)
        historical_paths.add(path)

    sweep_text = SWEEP_DOC.read_text(encoding="utf-8")
    for path in sorted(historical_paths):
        if path not in sweep_text:
            raise DocumentRegistryGuardError(f"conflict sweep missing historical path: {path}")
    for required in (
        "Status: CANONICAL CONFLICT SWEEP",
        "Classification: HISTORICAL_AUTHORITY_CONFLICT_REVIEW",
        "not active authority",
        "re-ratified",
        "document_registry.yaml",
    ):
        if required not in sweep_text:
            raise DocumentRegistryGuardError(f"conflict sweep missing required text: {required}")

    unregistered_claims = tuple(
        sorted(
            _scan_unregistered_authority_claims(
                registered_paths=registered_paths,
                historical_paths=historical_paths,
            )
        )
    )
    for code_surface, binding in sorted(code_surface_to_doc.items()):
        metadata = _extract_module_metadata(ROOT / code_surface)
        if metadata.get("doc_authority") != binding["id"]:
            module_metadata_mismatches.append(
                f"{code_surface}:doc_authority:{metadata.get('doc_authority')}!={binding['id']}"
            )
        if metadata.get("doc_version") != binding["version"]:
            module_version_mismatches.append(
                f"{code_surface}:doc_version:{metadata.get('doc_version')}!={binding['version']}"
            )
        module_invariants = tuple(metadata.get("governed_invariants", ()))
        if module_invariants != binding["invariants"]:
            module_metadata_mismatches.append(
                f"{code_surface}:invariants:{module_invariants}!={binding['invariants']}"
            )

    report = DocumentRegistryGuardReport(
        registry_path="afritech/governance/document_registry.yaml",
        registry_version=registry_version,
        registered_document_count=len(documents),
        historical_conflict_count=len(conflicts),
        compatibility_entry_count=len(compatibility_entries),
        root_navigation_doc=str(root_navigation["path"]),
        constitutional_root_doc=str(constitutional_root["path"]),
        architecture_root_doc=str(architecture_root["path"]),
        invariant_binding_count=invariant_binding_count,
        code_surface_binding_count=code_surface_binding_count,
        unregistered_authority_claims=unregistered_claims,
        unbound_registered_docs=tuple(sorted(unbound_registered_docs)),
        invalid_invariant_bindings=tuple(sorted(invalid_invariant_bindings)),
        invalid_code_surface_bindings=tuple(sorted(invalid_code_surface_bindings)),
        module_metadata_mismatches=tuple(sorted(module_metadata_mismatches)),
        module_version_mismatches=tuple(sorted(module_version_mismatches)),
    )
    if not report.clean:
        raise DocumentRegistryGuardError(
            "document authority binding drift detected: "
            + ", ".join(
                report.unregistered_authority_claims
                + report.unbound_registered_docs
                + report.invalid_invariant_bindings
                + report.invalid_code_surface_bindings
                + report.module_metadata_mismatches
                + report.module_version_mismatches
            )
        )
    return report


def _validate_protocol_compatibility(
    *,
    compatibility: Any,
    registry_version: str,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(compatibility, dict):
        raise DocumentRegistryGuardError("protocol compatibility block missing")
    current_version = str(compatibility.get("current_version", ""))
    verifier_version = str(compatibility.get("verifier_version", ""))
    entries = compatibility.get("versions")
    if current_version != registry_version:
        raise DocumentRegistryGuardError(
            "protocol compatibility current_version must match registry version"
        )
    if not verifier_version:
        raise DocumentRegistryGuardError("protocol compatibility verifier_version missing")
    if not isinstance(entries, list) or not entries:
        raise DocumentRegistryGuardError("protocol compatibility versions missing")
    normalized: list[dict[str, Any]] = []
    seen_versions: set[str] = set()
    current_present = False
    for entry in entries:
        if not isinstance(entry, dict):
            raise DocumentRegistryGuardError("protocol compatibility entry must be a mapping")
        version = str(entry.get("version", ""))
        status = str(entry.get("status", ""))
        breaking = entry.get("breaking")
        compatible_with = entry.get("compatible_with")
        if not _looks_like_semver(version):
            raise DocumentRegistryGuardError(
                f"invalid protocol compatibility version: {version}"
            )
        if version in seen_versions:
            raise DocumentRegistryGuardError(
                f"duplicate protocol compatibility version: {version}"
            )
        if not status:
            raise DocumentRegistryGuardError(
                f"protocol compatibility status missing for version: {version}"
            )
        if not isinstance(breaking, bool):
            raise DocumentRegistryGuardError(
                f"protocol compatibility breaking flag invalid for version: {version}"
            )
        if not isinstance(compatible_with, list) or not compatible_with:
            raise DocumentRegistryGuardError(
                f"protocol compatibility compatible_with missing for version: {version}"
            )
        for target in compatible_with:
            if not isinstance(target, str) or not _looks_like_version_pattern(target):
                raise DocumentRegistryGuardError(
                    f"invalid protocol compatibility target: {version}:{target}"
                )
        if version == current_version:
            current_present = True
            if "CURRENT" not in status:
                raise DocumentRegistryGuardError(
                    "current protocol version must declare CURRENT status"
                )
        seen_versions.add(version)
        normalized.append(entry)
    if not current_present:
        raise DocumentRegistryGuardError("current protocol version missing from compatibility")
    if verifier_version not in seen_versions:
        raise DocumentRegistryGuardError("verifier version missing from compatibility entries")
    return tuple(normalized)


def _scan_unregistered_authority_claims(
    *,
    registered_paths: set[str],
    historical_paths: set[str],
) -> list[str]:
    findings: list[str] = []
    allowlist = registered_paths | historical_paths
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.md")):
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowlist:
                continue
            snippet = "\n".join(path.read_text(encoding="utf-8", errors="ignore").splitlines()[:20])
            if any(pattern.search(snippet) for pattern in AUTHORITY_PATTERNS):
                findings.append(rel)
    return findings


def _require_single_document(
    documents: list[dict[str, Any]],
    authority: str,
) -> dict[str, Any]:
    matches = [entry for entry in documents if entry.get("authority") == authority]
    if len(matches) != 1:
        raise DocumentRegistryGuardError(
            f"expected exactly one {authority} document, found {len(matches)}"
        )
    return matches[0]


def _looks_like_semver(value: str) -> bool:
    return bool(re.fullmatch(r"\d+\.\d+\.\d+", value))


def _looks_like_version_pattern(value: str) -> bool:
    return bool(re.fullmatch(r"\d+\.\d+\.(?:\d+|x)", value))


def _require_exists(path: str) -> None:
    if not (ROOT / path).exists():
        raise DocumentRegistryGuardError(f"missing registered path: {path}")


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DocumentRegistryGuardError(f"{path} must contain a mapping")
    return payload


def _extract_module_metadata(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    metadata: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "__doc_authority__":
            metadata["doc_authority"] = ast.literal_eval(node.value)
        if target.id == "__doc_version__":
            metadata["doc_version"] = ast.literal_eval(node.value)
        if target.id == "__governed_invariants__":
            metadata["governed_invariants"] = tuple(ast.literal_eval(node.value))
    return metadata


def main() -> int:
    report = validate()
    print(
        "DOCUMENT_REGISTRY_GUARD: PASS "
        f"(registered={report.registered_document_count}, "
        f"historical_conflicts={report.historical_conflict_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
