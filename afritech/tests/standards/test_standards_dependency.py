from __future__ import annotations

from afritech.standards_dependency import (
    build_standard_conformance_profile,
    dependency_manifest_hash,
    register_protocol_dependency,
)


def test_standard_conformance_profile_is_deterministic() -> None:
    first = build_standard_conformance_profile()
    second = build_standard_conformance_profile()

    assert first == second
    assert first.protocol_version == "1.0.0"
    assert len(first.profile_hash) == 64


def test_register_protocol_dependency_builds_declarative_record() -> None:
    record = register_protocol_dependency(
        dependent_id="dep-sys-1",
        organization="Partner A",
        use_case="claims validation",
    )

    assert record.status == "DECLARED_DEPENDENCY"
    assert record.profile_id == "MULTI_PARTY_REPLAY_VERIFICATION_V1"
    assert len(record.dependency_hash) == 64


def test_dependency_manifest_hash_changes_with_dependents() -> None:
    first = register_protocol_dependency(
        dependent_id="dep-sys-1",
        organization="Partner A",
        use_case="claims validation",
    )
    second = register_protocol_dependency(
        dependent_id="dep-sys-2",
        organization="Partner B",
        use_case="audit retention",
    )

    assert dependency_manifest_hash((first,)) != dependency_manifest_hash((first, second))
