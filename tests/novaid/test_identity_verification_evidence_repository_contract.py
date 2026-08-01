from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timezone
from inspect import signature
from uuid import uuid4

import pytest

from afritech.novaid.persistence.identity_verification_evidence_repository import (
    FORBIDDEN_EVIDENCE_REFERENCE_FIELDS,
    IdentityVerificationEvidenceReference,
    IdentityVerificationEvidenceRepository,
    IdentityVerificationEvidenceType,
)


def uid() -> str:
    return str(uuid4())


def reference(
    **overrides: object,
) -> IdentityVerificationEvidenceReference:
    values: dict[str, object] = {
        "tenant_id": uid(),
        "verification_id": uid(),
        "evidence_type": (
            IdentityVerificationEvidenceType.OCR_EXTRACTION
        ),
        "evidence_id": uid(),
        "evidence_version": 1,
        "collected_at": datetime(
            2026,
            8,
            1,
            8,
            0,
            0,
            tzinfo=timezone.utc,
        ),
        "metadata": {
            "algorithm_version": "ocr-v1",
        },
    }
    values.update(overrides)

    return IdentityVerificationEvidenceReference(
        **values
    )


def test_evidence_types_are_canonical() -> None:
    assert {
        item.value
        for item in IdentityVerificationEvidenceType
    } == {
        "OCR_EXTRACTION",
        "DOCUMENT_AUTHENTICITY",
        "DOCUMENT_SELFIE_MATCH",
        "LIVENESS_ASSESSMENT",
    }


def test_reference_is_immutable_dataclass() -> None:
    current = reference()

    assert is_dataclass(current)

    with pytest.raises(FrozenInstanceError):
        current.evidence_id = uid()  # type: ignore[misc]


def test_reference_normalizes_required_text() -> None:
    current = reference(
        tenant_id=" tenant-1 ",
        verification_id=" verification-1 ",
        evidence_id=" evidence-1 ",
    )

    assert current.tenant_id == "tenant-1"
    assert current.verification_id == "verification-1"
    assert current.evidence_id == "evidence-1"


@pytest.mark.parametrize(
    ("field_name", "error_code"),
    (
        ("tenant_id", "TENANT_ID_REQUIRED"),
        (
            "verification_id",
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        ),
        (
            "evidence_id",
            "IDENTITY_VERIFICATION_EVIDENCE_ID_REQUIRED",
        ),
    ),
)
def test_blank_required_text_is_rejected(
    field_name: str,
    error_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=error_code,
    ):
        reference(
            **{field_name: " "}
        )


@pytest.mark.parametrize(
    "evidence_version",
    (
        0,
        -1,
        True,
        1.5,
    ),
)
def test_invalid_evidence_version_is_rejected(
    evidence_version: object,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "INVALID_IDENTITY_VERIFICATION_"
            "EVIDENCE_VERSION"
        ),
    ):
        reference(
            evidence_version=evidence_version
        )


def test_invalid_evidence_type_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "INVALID_IDENTITY_VERIFICATION_"
            "EVIDENCE_TYPE"
        ),
    ):
        reference(
            evidence_type="OCR_EXTRACTION"
        )


@pytest.mark.parametrize(
    "collected_at",
    (
        "2026-08-01T08:00:00+00:00",
        datetime(2026, 8, 1, 8, 0, 0),
        None,
    ),
)
def test_invalid_collection_timestamp_is_rejected(
    collected_at: object,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "IDENTITY_VERIFICATION_EVIDENCE_"
            "TIMESTAMP_REQUIRED"
        ),
    ):
        reference(
            collected_at=collected_at
        )


def test_metadata_is_defensively_copied() -> None:
    metadata = {
        "algorithm_version": "ocr-v1",
    }

    current = reference(
        metadata=metadata
    )

    metadata["algorithm_version"] = "changed"

    assert current.metadata == {
        "algorithm_version": "ocr-v1",
    }


def test_metadata_mapping_is_immutable() -> None:
    current = reference()

    with pytest.raises(TypeError):
        current.metadata["new"] = "value"  # type: ignore[index]


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64"},
        {"provider_payload": {"status": "PASS"}},
        {"nested": {"raw_selfie": "base64"}},
        {"items": [{"face_embedding": [0.1]}]},
        {"api_key": "secret"},
        {"private_key": "secret"},
    ),
)
def test_raw_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "RAW_EVIDENCE_REFERENCE_"
            "MATERIAL_FORBIDDEN"
        ),
    ):
        reference(metadata=metadata)


def test_forbidden_registry_covers_sensitive_fields() -> None:
    expected = {
        "raw_image",
        "raw_document",
        "raw_selfie",
        "raw_video",
        "raw_mrz",
        "barcode_payload",
        "provider_payload",
        "face_embedding",
        "biometric_template",
        "api_key",
        "private_key",
        "access_token",
        "password",
    }

    assert expected.issubset(
        FORBIDDEN_EVIDENCE_REFERENCE_FIELDS
    )


def test_repository_protocol_is_runtime_checkable() -> None:
    class Repository:
        def add_evidence_reference(
            self,
            reference: IdentityVerificationEvidenceReference,
        ) -> None:
            return None

        def get_evidence_reference(
            self,
            *,
            tenant_id: str,
            verification_id: str,
            evidence_type: IdentityVerificationEvidenceType,
        ) -> IdentityVerificationEvidenceReference | None:
            return None

        def list_verification_evidence(
            self,
            *,
            tenant_id: str,
            verification_id: str,
        ) -> tuple[
            IdentityVerificationEvidenceReference,
            ...,
        ]:
            return ()

        def evidence_reference_exists(
            self,
            *,
            tenant_id: str,
            verification_id: str,
            evidence_type: IdentityVerificationEvidenceType,
        ) -> bool:
            return False

    assert isinstance(
        Repository(),
        IdentityVerificationEvidenceRepository,
    )


def test_invalid_repository_does_not_satisfy_protocol() -> None:
    class InvalidRepository:
        pass

    assert not isinstance(
        InvalidRepository(),
        IdentityVerificationEvidenceRepository,
    )


def test_repository_contract_exposes_required_methods() -> None:
    required = {
        "add_evidence_reference",
        "get_evidence_reference",
        "list_verification_evidence",
        "evidence_reference_exists",
    }

    assert required.issubset(
        set(dir(IdentityVerificationEvidenceRepository))
    )


def test_repository_methods_are_tenant_scoped() -> None:
    for method_name in (
        "get_evidence_reference",
        "list_verification_evidence",
        "evidence_reference_exists",
    ):
        parameters = signature(
            getattr(
                IdentityVerificationEvidenceRepository,
                method_name,
            )
        ).parameters

        assert "tenant_id" in parameters
        assert "verification_id" in parameters


def test_list_return_annotation_is_immutable_tuple() -> None:
    annotation = signature(
        IdentityVerificationEvidenceRepository
        .list_verification_evidence
    ).return_annotation

    assert "tuple" in str(annotation)


def test_reference_contains_no_raw_material_fields() -> None:
    field_names = {
        item
        for item in (
            "raw_image",
            "raw_document",
            "raw_selfie",
            "provider_payload",
            "face_embedding",
            "biometric_template",
        )
        if hasattr(
            IdentityVerificationEvidenceReference,
            item,
        )
    }

    assert not field_names
