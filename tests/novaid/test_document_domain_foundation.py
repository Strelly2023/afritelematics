from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    BarcodeEvidence,
    BarcodeType,
    BiometricPurpose,
    CaptureChannel,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    DocumentAuthenticityDecision,
    DocumentAuthenticityEvidence,
    DocumentCaptureChannel,
    DocumentCaptureReference,
    DocumentExtractedData,
    DocumentSide,
    DocumentVerificationDecision,
    DocumentVerificationEvidence,
    DocumentVerificationStatus,
    IdentityDocument,
    IdentityDocumentType,
    MachineReadableZoneEvidence,
    MachineReadableZoneType,
    OCRField,
    OCRFieldType,
)


def uid() -> str:
    return str(uuid4())


def checksum() -> str:
    return "a" * 64


def capture() -> DocumentCaptureReference:
    return DocumentCaptureReference(
        capture_id=uid(),
        side=DocumentSide.BIO_DATA_PAGE,
        channel=DocumentCaptureChannel.MOBILE_CAMERA,
        encrypted_object_reference=(
            "vault://documents/capture-reference"
        ),
        media_type="image/jpeg",
        checksum_sha256=checksum(),
        capture_device=CaptureDevice(
            device_reference="document-device",
            channel=CaptureChannel.MOBILE_APP,
            integrity_verified=True,
        ),
        capture_environment=CaptureEnvironment(
            country_code="AU",
        ),
        capture_quality=CaptureQuality(
            overall_score=0.94,
            face_detected=True,
            single_subject_detected=True,
        ),
    )


def mrz() -> MachineReadableZoneEvidence:
    return MachineReadableZoneEvidence(
        mrz_type=MachineReadableZoneType.TD3,
        document_code="P",
        issuing_country_code="AUS",
        document_number="N1234567",
        nationality_code="AUS",
        date_of_birth="1990-01-01",
        expiry_date="2030-01-01",
        checksums_valid=True,
        confidence_score=0.98,
        provider_reference="mrz-provider-reference",
        algorithm_version="mrz-model-1.0",
    )


def authenticity() -> DocumentAuthenticityEvidence:
    return DocumentAuthenticityEvidence(
        decision=DocumentAuthenticityDecision.AUTHENTIC,
        overall_score=0.95,
        tampering_score=0.03,
        security_feature_score=0.94,
        hologram_score=0.91,
        portrait_integrity_score=0.96,
        mrz_consistent=True,
        barcode_consistent=True,
        provider_reference="authenticity-provider-reference",
        algorithm_version="document-model-1.0",
    )


def document(
    *,
    status: DocumentVerificationStatus = (
        DocumentVerificationStatus.PENDING
    ),
    verified_at: datetime | None = None,
) -> IdentityDocument:
    return IdentityDocument(
        document_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code=" au ",
        status=status,
        purpose=BiometricPurpose.EKYC,
        document_number_reference=(
            "vault://document-number/reference"
        ),
        captures=(capture(),),
        extracted_data=DocumentExtractedData(
            document_number="N1234567",
            given_names=("Djuma",),
            family_name="Kikombe",
            date_of_birth="1990-01-01",
            date_of_issue="2020-01-01",
            date_of_expiry="2030-01-01",
            nationality_code="COD",
            issuing_country_code="AU",
        ),
        mrz_evidence=mrz(),
        authenticity_evidence=authenticity(),
        provider_reference="document-provider-reference",
        algorithm_version="document-model-1.0",
        issued_at=date(2020, 1, 1),
        expires_at=date(2030, 1, 1),
        verified_at=verified_at,
    )


def test_document_capture_stores_reference_not_raw_image() -> None:
    current = capture()

    assert current.encrypted_object_reference.startswith(
        "vault://"
    )
    assert not hasattr(current, "raw_image")
    assert not hasattr(current, "image_bytes")
    assert not hasattr(current, "video")


def test_capture_checksum_is_validated() -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_DOCUMENT_CHECKSUM",
    ):
        DocumentCaptureReference(
            capture_id=uid(),
            side=DocumentSide.FRONT,
            channel=DocumentCaptureChannel.FILE_UPLOAD,
            encrypted_object_reference=(
                "vault://documents/reference"
            ),
            media_type="image/jpeg",
            checksum_sha256="invalid",
        )


def test_capture_values_are_normalized() -> None:
    current = DocumentCaptureReference(
        capture_id="  capture-reference  ",
        side="FRONT",
        channel="FILE_UPLOAD",
        encrypted_object_reference=(
            "  vault://documents/reference  "
        ),
        media_type=" IMAGE/JPEG ",
        checksum_sha256=checksum().upper(),
    )

    assert current.capture_id == "capture-reference"
    assert current.media_type == "image/jpeg"
    assert current.checksum_sha256 == checksum()


def test_ocr_field_normalizes_and_validates_score() -> None:
    field = OCRField(
        field_type=OCRFieldType.FAMILY_NAME,
        value="  Kikombe  ",
        confidence_score=0.97,
    )

    assert field.value == "Kikombe"

    with pytest.raises(
        ValueError,
        match="INVALID_OCR_CONFIDENCE_SCORE",
    ):
        OCRField(
            field_type=OCRFieldType.FAMILY_NAME,
            value="Kikombe",
            confidence_score=1.1,
        )


def test_mrz_evidence_normalizes_values() -> None:
    evidence = mrz()

    assert evidence.document_code == "P"
    assert evidence.document_number == "N1234567"
    assert evidence.date_of_birth == date(1990, 1, 1)
    assert evidence.expiry_date == date(2030, 1, 1)


def test_barcode_evidence_stores_extracted_fields() -> None:
    field = OCRField(
        field_type=OCRFieldType.DOCUMENT_NUMBER,
        value="DL123456",
        confidence_score=0.96,
    )

    evidence = BarcodeEvidence(
        barcode_type=BarcodeType.PDF417,
        checksum_valid=True,
        confidence_score=0.97,
        provider_reference="barcode-provider",
        algorithm_version="barcode-model-1.0",
        extracted_fields=(field,),
    )

    assert evidence.extracted_fields == (field,)


def test_extracted_data_normalizes_country_and_dates() -> None:
    extracted = DocumentExtractedData(
        document_number="  N1234567  ",
        given_names=(" Djuma ", " "),
        family_name=" Kikombe ",
        date_of_issue="2020-01-01",
        date_of_expiry="2030-01-01",
        issuing_country_code=" au ",
    )

    assert extracted.document_number == "N1234567"
    assert extracted.given_names == ("Djuma",)
    assert extracted.family_name == "Kikombe"
    assert extracted.issuing_country_code == "AU"


def test_extracted_data_rejects_invalid_validity_period() -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_DOCUMENT_VALIDITY_PERIOD",
    ):
        DocumentExtractedData(
            date_of_issue="2030-01-01",
            date_of_expiry="2029-01-01",
        )


def test_identity_document_normalizes_country_code() -> None:
    current = document()

    assert current.issuing_country_code == "AU"


@pytest.mark.parametrize(
    "country_code",
    (
        "",
        "A",
        "AUS",
        "12",
        "A1",
    ),
)
def test_identity_document_rejects_invalid_country(
    country_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_COUNTRY_CODE",
    ):
        IdentityDocument(
            document_id=uid(),
            tenant_id=uid(),
            identity_id=uid(),
            document_type=IdentityDocumentType.PASSPORT,
            issuing_country_code=country_code,
        )


def test_document_lifecycle_is_versioned() -> None:
    pending = document()

    in_progress = pending.transition(
        DocumentVerificationStatus.IN_PROGRESS
    )
    review = in_progress.transition(
        DocumentVerificationStatus.MANUAL_REVIEW
    )
    verified = review.transition(
        DocumentVerificationStatus.VERIFIED
    )

    assert pending.version == 1
    assert in_progress.version == 2
    assert review.version == 3
    assert verified.version == 4
    assert verified.verified_at is not None


def test_invalid_document_transition_fails_closed() -> None:
    pending = document()

    with pytest.raises(
        ValueError,
        match="INVALID_DOCUMENT_STATUS_TRANSITION",
    ):
        pending.transition(
            DocumentVerificationStatus.VERIFIED
        )


def test_verified_document_requires_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="DOCUMENT_VERIFIED_AT_REQUIRED",
    ):
        document(
            status=DocumentVerificationStatus.VERIFIED,
            verified_at=None,
        )


def test_duplicate_capture_is_rejected() -> None:
    current_capture = capture()

    with pytest.raises(
        ValueError,
        match="DUPLICATE_DOCUMENT_CAPTURE",
    ):
        IdentityDocument(
            document_id=uid(),
            tenant_id=uid(),
            identity_id=uid(),
            document_type=IdentityDocumentType.PASSPORT,
            issuing_country_code="AU",
            captures=(
                current_capture,
                current_capture,
            ),
        )


def test_document_expiry_is_evaluated() -> None:
    current = document()

    assert current.is_expired(
        at=date(2029, 1, 1)
    ) is False
    assert current.is_expired(
        at=date(2030, 1, 1)
    ) is True


def test_document_verification_evidence_is_immutable() -> None:
    evidence = DocumentVerificationEvidence(
        evidence_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        document_id=uid(),
        decision=DocumentVerificationDecision.PASS,
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code="AU",
        provider_reference="document-provider",
        algorithm_version="document-model-1.0",
        overall_score=0.96,
        authenticity_score=0.95,
        data_consistency_score=0.94,
        portrait_reference="vault://portrait/reference",
    )

    with pytest.raises(FrozenInstanceError):
        evidence.decision = (  # type: ignore[misc]
            DocumentVerificationDecision.FAIL
        )


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64"},
        {"raw_selfie": "base64"},
        {"raw_video": "blob"},
        {"embedding": [0.1, 0.2]},
        {"feature_vector": [1, 2]},
        {"nfc_dump": "secret"},
        {"barcode_payload": "raw"},
        {"provider_secret": "secret"},
    ),
)
def test_raw_document_material_is_rejected(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match="RAW_DOCUMENT_MATERIAL_FORBIDDEN",
    ):
        IdentityDocument(
            document_id=uid(),
            tenant_id=uid(),
            identity_id=uid(),
            document_type=IdentityDocumentType.PASSPORT,
            issuing_country_code="AU",
            metadata=metadata,
        )


def test_document_models_are_immutable() -> None:
    current = document()

    with pytest.raises(FrozenInstanceError):
        current.status = (  # type: ignore[misc]
            DocumentVerificationStatus.VERIFIED
        )


def test_metadata_is_defensively_copied() -> None:
    metadata = {
        "source": "controlled-pilot",
    }

    current = IdentityDocument(
        document_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code="AU",
        metadata=metadata,
    )

    metadata["source"] = "changed"

    assert current.metadata == {
        "source": "controlled-pilot",
    }
