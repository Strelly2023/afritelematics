from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    CaptureChannel,
    CaptureDecision,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    DocumentCaptureChannel,
    DocumentCaptureReference,
    DocumentExtractedData,
    DocumentOCRService,
    DocumentSide,
    DocumentVerificationStatus,
    IdentityDocument,
    IdentityDocumentType,
    MachineReadableZoneEvidence,
    MachineReadableZoneType,
    OCRExtractionDecision,
    OCRExtractionEvent,
    OCRExtractionPolicy,
    OCRExtractionSource,
    OCRField,
    OCRFieldType,
    OCRProviderEvidence,
    RequestContext,
    Tenant,
    TenantSecurityPolicy,
)


def uid() -> str:
    return str(uuid4())


def request_context(
    tenant_id: str,
) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_identity_id=uid(),
        actor_membership_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        authentication_strength="PASSKEY",
    )


def tenant(
    tenant_id: str,
    *,
    require_integrity: bool = False,
) -> Tenant:
    return Tenant(
        tenant_id=tenant_id,
        name="Document OCR Tenant",
        security_policy=TenantSecurityPolicy(
            device_binding_required=require_integrity,
        ),
    )


def capture(
    *,
    integrity_verified: bool = True,
    emulator_detected: bool = False,
    rooted_or_jailbroken: bool = False,
    quality_score: float = 0.94,
    quality_decision: CaptureDecision = (
        CaptureDecision.ACCEPT
    ),
) -> DocumentCaptureReference:
    return DocumentCaptureReference(
        capture_id=uid(),
        side=DocumentSide.BIO_DATA_PAGE,
        channel=DocumentCaptureChannel.MOBILE_CAMERA,
        encrypted_object_reference=(
            "vault://documents/capture-reference"
        ),
        media_type="image/jpeg",
        checksum_sha256="a" * 64,
        capture_device=CaptureDevice(
            device_reference="document-device",
            channel=CaptureChannel.MOBILE_APP,
            integrity_verified=integrity_verified,
        ),
        capture_environment=CaptureEnvironment(
            country_code="AU",
            emulator_detected=emulator_detected,
            rooted_or_jailbroken=(
                rooted_or_jailbroken
            ),
        ),
        capture_quality=CaptureQuality(
            overall_score=quality_score,
            face_detected=True,
            single_subject_detected=True,
            minimum_required_score=0.70,
            decision=quality_decision,
        ),
    )


def document(
    tenant_id: str,
    identity_id: str,
    *,
    document_type: IdentityDocumentType = (
        IdentityDocumentType.PASSPORT
    ),
    status: DocumentVerificationStatus = (
        DocumentVerificationStatus.PENDING
    ),
    current_capture: DocumentCaptureReference | None = None,
) -> IdentityDocument:
    return IdentityDocument(
        document_id=uid(),
        tenant_id=tenant_id,
        identity_id=identity_id,
        document_type=document_type,
        issuing_country_code="AU",
        status=status,
        captures=(
            (current_capture or capture()),
        ),
    )


def passport_fields(
    *,
    confidence: float = 0.96,
) -> tuple[OCRField, ...]:
    return (
        OCRField(
            field_type=OCRFieldType.DOCUMENT_NUMBER,
            value="N1234567",
            confidence_score=confidence,
        ),
        OCRField(
            field_type=OCRFieldType.FAMILY_NAME,
            value="Kikombe",
            confidence_score=confidence,
        ),
        OCRField(
            field_type=OCRFieldType.GIVEN_NAMES,
            value="Djuma",
            confidence_score=confidence,
        ),
        OCRField(
            field_type=OCRFieldType.DATE_OF_BIRTH,
            value="1990-01-01",
            normalized_value="1990-01-01",
            confidence_score=confidence,
        ),
        OCRField(
            field_type=OCRFieldType.DATE_OF_EXPIRY,
            value="2030-01-01",
            normalized_value="2030-01-01",
            confidence_score=confidence,
        ),
    )


def mrz(
    *,
    checksums_valid: bool = True,
) -> MachineReadableZoneEvidence:
    return MachineReadableZoneEvidence(
        mrz_type=MachineReadableZoneType.TD3,
        document_code="P",
        issuing_country_code="AUS",
        document_number="N1234567",
        nationality_code="COD",
        date_of_birth="1990-01-01",
        expiry_date="2030-01-01",
        checksums_valid=checksums_valid,
        confidence_score=0.98,
        provider_reference="mrz-provider-reference",
        algorithm_version="mrz-model-1.0",
    )


def evidence(
    *,
    document_type: IdentityDocumentType = (
        IdentityDocumentType.PASSPORT
    ),
    confidence: float = 0.96,
    fields: tuple[OCRField, ...] | None = None,
    mrz_evidence: MachineReadableZoneEvidence | None = None,
    expiry: date | None = date(2030, 1, 1),
    metadata: dict[str, object] | None = None,
) -> OCRProviderEvidence:
    return OCRProviderEvidence(
        provider_reference="ocr-provider-reference",
        provider_decision_reference="ocr-decision-001",
        algorithm_version="ocr-model-1.0",
        source=OCRExtractionSource.COMBINED,
        document_type=document_type,
        overall_confidence_score=confidence,
        fields=(
            fields
            if fields is not None
            else passport_fields()
        ),
        extracted_data=DocumentExtractedData(
            document_number="N1234567",
            given_names=("Djuma",),
            family_name="Kikombe",
            date_of_birth=date(1990, 1, 1),
            date_of_issue=date(2020, 1, 1),
            date_of_expiry=expiry,
            nationality_code="COD",
            issuing_country_code="AU",
        ),
        mrz_evidence=(
            mrz_evidence
            if mrz_evidence is not None
            else mrz()
        ),
        metadata=dict(metadata or {}),
    )


def extract(
    *,
    tenant_id: str,
    identity_id: str,
    current_document: IdentityDocument | None = None,
    current_evidence: OCRProviderEvidence | None = None,
    current_tenant: Tenant | None = None,
    policy: OCRExtractionPolicy | None = None,
):
    active_document = (
        current_document
        or document(
            tenant_id,
            identity_id,
        )
    )

    return DocumentOCRService().extract(
        context=request_context(tenant_id),
        tenant=current_tenant or tenant(tenant_id),
        document=active_document,
        evidence=current_evidence or evidence(),
        expected_version=active_document.version,
        policy=policy,
    )


def test_high_confidence_passport_ocr_is_accepted() -> None:
    tenant_id = uid()
    identity_id = uid()

    result = extract(
        tenant_id=tenant_id,
        identity_id=identity_id,
    )

    assert (
        result.extraction.decision
        is OCRExtractionDecision.ACCEPT
    )
    assert (
        result.document.status
        is DocumentVerificationStatus.IN_PROGRESS
    )
    assert result.document.version == 2
    assert result.document.extracted_data is not None
    assert (
        result.document.extracted_data.document_number
        == "N1234567"
    )


@pytest.mark.parametrize(
    ("confidence", "expected"),
    (
        (
            0.75,
            OCRExtractionDecision.MANUAL_REVIEW,
        ),
        (
            0.40,
            OCRExtractionDecision.RECAPTURE,
        ),
        (
            0.00,
            OCRExtractionDecision.REJECT,
        ),
    ),
)
def test_confidence_decisions(
    confidence: float,
    expected: OCRExtractionDecision,
) -> None:
    tenant_id = uid()

    result = extract(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(
            confidence=confidence,
            fields=passport_fields(
                confidence=confidence,
            ),
        ),
    )

    assert result.extraction.decision is expected


def test_manual_review_updates_document_status() -> None:
    tenant_id = uid()

    result = extract(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(
            confidence=0.75,
            fields=passport_fields(
                confidence=0.75,
            ),
        ),
    )

    assert (
        result.document.status
        is DocumentVerificationStatus.MANUAL_REVIEW
    )


def test_missing_required_field_requests_recapture() -> None:
    tenant_id = uid()

    incomplete_fields = tuple(
        field
        for field in passport_fields()
        if field.field_type
        is not OCRFieldType.DOCUMENT_NUMBER
    )

    incomplete_data = OCRProviderEvidence(
        provider_reference="ocr-provider",
        algorithm_version="ocr-model-1.0",
        source=OCRExtractionSource.COMBINED,
        document_type=IdentityDocumentType.PASSPORT,
        overall_confidence_score=0.96,
        fields=incomplete_fields,
        extracted_data=DocumentExtractedData(
            family_name="Kikombe",
            date_of_birth="1990-01-01",
            date_of_expiry="2030-01-01",
        ),
        mrz_evidence=mrz(),
    )

    result = extract(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=incomplete_data,
    )

    assert (
        result.extraction.decision
        is OCRExtractionDecision.RECAPTURE
    )
    assert (
        "MISSING_DOCUMENT_NUMBER"
        in result.extraction.reason_codes
    )


def test_missing_passport_mrz_requires_review() -> None:
    tenant_id = uid()

    without_mrz = evidence()
    without_mrz = replace(
        without_mrz,
        mrz_evidence=None,
    )

    result = extract(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=without_mrz,
    )

    assert (
        result.extraction.decision
        is OCRExtractionDecision.MANUAL_REVIEW
    )
    assert result.extraction.reason_codes == (
        "PASSPORT_MRZ_REQUIRED",
    )


def test_invalid_mrz_checksum_is_rejected() -> None:
    tenant_id = uid()

    result = extract(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(
            mrz_evidence=mrz(
                checksums_valid=False,
            ),
        ),
    )

    assert (
        result.extraction.decision
        is OCRExtractionDecision.REJECT
    )
    assert result.extraction.reason_codes == (
        "MRZ_CHECKSUM_INVALID",
    )


def test_expired_document_is_rejected() -> None:
    tenant_id = uid()

    result = extract(
        tenant_id=tenant_id,
        identity_id=uid(),
        current_evidence=evidence(
            expiry=date.today() - timedelta(days=1),
        ),
    )

    assert (
        result.extraction.decision
        is OCRExtractionDecision.REJECT
    )
    assert result.extraction.reason_codes == (
        "DOCUMENT_EXPIRED",
    )


def test_cross_tenant_request_fails_closed() -> None:
    tenant_id = uid()
    identity_id = uid()
    current = document(
        tenant_id,
        identity_id,
    )

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        DocumentOCRService().extract(
            context=request_context(uid()),
            tenant=tenant(tenant_id),
            document=current,
            evidence=evidence(),
            expected_version=current.version,
        )


def test_document_tenant_mismatch_fails_closed() -> None:
    tenant_id = uid()

    with pytest.raises(
        PermissionError,
        match="DOCUMENT_TENANT_MISMATCH",
    ):
        extract(
            tenant_id=tenant_id,
            identity_id=uid(),
            current_document=document(
                uid(),
                uid(),
            ),
        )


def test_stale_document_version_is_rejected() -> None:
    tenant_id = uid()
    current = document(
        tenant_id,
        uid(),
    )

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        DocumentOCRService().extract(
            context=request_context(tenant_id),
            tenant=tenant(tenant_id),
            document=current,
            evidence=evidence(),
            expected_version=current.version + 1,
        )


def test_document_type_mismatch_is_rejected() -> None:
    tenant_id = uid()

    with pytest.raises(
        ValueError,
        match="OCR_DOCUMENT_TYPE_MISMATCH",
    ):
        extract(
            tenant_id=tenant_id,
            identity_id=uid(),
            current_evidence=evidence(
                document_type=(
                    IdentityDocumentType.DRIVER_LICENCE
                ),
            ),
        )


def test_document_capture_is_required() -> None:
    tenant_id = uid()
    current = document(
        tenant_id,
        uid(),
    )
    current = replace(
        current,
        captures=(),
    )

    with pytest.raises(
        ValueError,
        match="DOCUMENT_CAPTURE_REQUIRED",
    ):
        extract(
            tenant_id=tenant_id,
            identity_id=current.identity_id,
            current_document=current,
        )


def test_terminal_document_is_not_available_for_ocr() -> None:
    tenant_id = uid()
    now = datetime.now(UTC)

    current = document(
        tenant_id,
        uid(),
    )

    current = replace(
        current,
        status=DocumentVerificationStatus.VERIFIED,
        verified_at=now,
    )

    with pytest.raises(
        ValueError,
        match="DOCUMENT_NOT_AVAILABLE_FOR_OCR",
    ):
        extract(
            tenant_id=tenant_id,
            identity_id=current.identity_id,
            current_document=current,
        )


def test_device_integrity_policy_is_enforced() -> None:
    tenant_id = uid()
    current = document(
        tenant_id,
        uid(),
        current_capture=capture(
            integrity_verified=False,
        ),
    )

    with pytest.raises(
        PermissionError,
        match="CAPTURE_DEVICE_INTEGRITY_REQUIRED",
    ):
        extract(
            tenant_id=tenant_id,
            identity_id=current.identity_id,
            current_document=current,
            current_tenant=tenant(
                tenant_id,
                require_integrity=True,
            ),
        )


@pytest.mark.parametrize(
    ("current_capture", "error"),
    (
        (
            capture(emulator_detected=True),
            "DOCUMENT_CAPTURE_EMULATOR_DENIED",
        ),
        (
            capture(rooted_or_jailbroken=True),
            "DOCUMENT_CAPTURE_COMPROMISED_DEVICE_DENIED",
        ),
    ),
)
def test_compromised_capture_is_rejected(
    current_capture: DocumentCaptureReference,
    error: str,
) -> None:
    tenant_id = uid()
    current = document(
        tenant_id,
        uid(),
        current_capture=current_capture,
    )

    with pytest.raises(
        PermissionError,
        match=error,
    ):
        extract(
            tenant_id=tenant_id,
            identity_id=current.identity_id,
            current_document=current,
        )


def test_capture_quality_policy_is_enforced() -> None:
    tenant_id = uid()
    current = document(
        tenant_id,
        uid(),
        current_capture=capture(
            quality_score=0.75,
        ),
    )

    with pytest.raises(
        ValueError,
        match="DOCUMENT_CAPTURE_QUALITY_BELOW_POLICY",
    ):
        extract(
            tenant_id=tenant_id,
            identity_id=current.identity_id,
            current_document=current,
            policy=OCRExtractionPolicy(
                minimum_capture_quality_score=0.80,
            ),
        )


def test_duplicate_ocr_field_type_is_rejected() -> None:
    duplicated = passport_fields() + (
        OCRField(
            field_type=OCRFieldType.DOCUMENT_NUMBER,
            value="SECOND",
            confidence_score=0.90,
        ),
    )

    with pytest.raises(
        ValueError,
        match="DUPLICATE_OCR_FIELD_TYPE",
    ):
        evidence(fields=duplicated)


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64"},
        {"raw_text": "full OCR output"},
        {"provider_payload": {"secret": "value"}},
        {"barcode_payload": "raw"},
        {"mrz_raw": "raw"},
        {"nfc_dump": "raw"},
        {"provider_secret": "secret"},
    ),
)
def test_raw_provider_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="RAW_DOCUMENT_MATERIAL_FORBIDDEN",
    ):
        evidence(metadata=metadata)


def test_ocr_event_is_traceable() -> None:
    tenant_id = uid()
    identity_id = uid()
    context = request_context(tenant_id)
    current = document(
        tenant_id,
        identity_id,
    )

    result = DocumentOCRService().extract(
        context=context,
        tenant=tenant(tenant_id),
        document=current,
        evidence=evidence(),
        expected_version=current.version,
    )

    event = result.event

    assert isinstance(event, OCRExtractionEvent)
    assert event.actor_identity_id == (
        context.actor_identity_id
    )
    assert event.correlation_id == (
        context.correlation_id
    )
    assert event.request_id == context.request_id
    assert event.event_type == "OCR_EXTRACTION_ACCEPT"


def test_result_record_and_event_are_immutable() -> None:
    tenant_id = uid()

    result = extract(
        tenant_id=tenant_id,
        identity_id=uid(),
    )

    with pytest.raises(FrozenInstanceError):
        result.extraction = result.extraction  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.event.event_type = "CHANGED"  # type: ignore[misc]


def test_ocr_domain_contains_no_raw_material() -> None:
    current = evidence()

    assert not hasattr(current, "raw_image")
    assert not hasattr(current, "image_bytes")
    assert not hasattr(current, "raw_text")
    assert not hasattr(current, "provider_payload")
    assert not hasattr(current, "mrz_raw")
    assert not hasattr(current, "barcode_payload")


@pytest.mark.parametrize(
    ("review", "acceptance"),
    (
        (0.85, 0.85),
        (0.90, 0.85),
    ),
)
def test_invalid_threshold_order_is_rejected(
    review: float,
    acceptance: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_OCR_THRESHOLD_ORDER",
    ):
        OCRExtractionPolicy(
            manual_review_threshold=review,
            acceptance_threshold=acceptance,
        )
