"""Runtime certificate validator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class CertificateValidationError(RuntimeError):
    """Raised when a runtime certificate is invalid."""


@dataclass(frozen=True)
class CertificateValidationResult:
    valid: bool
    reason: str
    certificate_path: str
    epoch: int | None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "certificate_path": self.certificate_path,
            "epoch": self.epoch,
        }


DEFAULT_CERTIFICATE_CANDIDATES = (
    Path("afritech/proof/certificates/runtime_epoch_0006.cert"),
    Path("afritech/proof/runtime_certificate.json"),
    Path("certificates/runtime_epoch_6.json"),
    Path("afritech/proof/certificates/runtime_epoch_6.json"),
    Path("afritech/certification/runtime_epoch_6.json"),
)

LEGACY_REQUIRED_FIELDS = {"certificate_type", "epoch", "status"}


def validate_certificate(
    certificate_path: str | Path,
    *,
    expected_epoch: int | None = None,
) -> CertificateValidationResult:
    path = Path(certificate_path)

    if not path.exists():
        raise CertificateValidationError(f"certificate not found: {path}")

    if not path.is_file():
        raise CertificateValidationError(f"certificate path is not a file: {path}")

    if not _is_runtime_certificate_filename(path.name):
        raise CertificateValidationError(
            "runtime certificate filename must be 'runtime_certificate.json' "
            "or start with 'runtime_epoch_'"
        )

    payload = _read_certificate_payload(path)
    epoch = _validate_supported_certificate(payload, path, expected_epoch)

    return CertificateValidationResult(
        valid=True,
        reason="certificate_valid",
        certificate_path=str(path),
        epoch=epoch,
    )


def require_valid_certificate(
    certificate_path: str | Path,
    *,
    expected_epoch: int | None = None,
) -> CertificateValidationResult:
    return validate_certificate(certificate_path, expected_epoch=expected_epoch)


def find_default_certificate() -> Path:
    for path in DEFAULT_CERTIFICATE_CANDIDATES:
        if path.exists() and path.is_file():
            return path

    raise CertificateValidationError(
        "certificate not found in known locations: "
        + ", ".join(str(path) for path in DEFAULT_CERTIFICATE_CANDIDATES)
    )


def _read_certificate_payload(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8").strip()

    if not text:
        raise CertificateValidationError(f"certificate is empty: {path}")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = _parse_key_value_certificate(text)

    if not isinstance(payload, dict):
        raise CertificateValidationError("certificate payload must be an object")

    return payload


def _parse_key_value_certificate(text: str) -> Mapping[str, Any]:
    payload: dict[str, Any] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            continue

        payload[key.strip()] = _coerce_scalar(value.strip())

    if not payload:
        raise CertificateValidationError(
            "certificate is neither JSON nor key/value certificate format"
        )

    return payload


def _coerce_scalar(value: str) -> object:
    lowered = value.lower()

    if lowered in {"true", "false"}:
        return lowered == "true"

    if value.isdigit():
        return int(value)

    return value.strip('"').strip("'")


def _validate_supported_certificate(
    payload: Mapping[str, Any],
    path: Path,
    expected_epoch: int | None,
) -> int | None:
    if LEGACY_REQUIRED_FIELDS.issubset(payload):
        return _validate_legacy_certificate(payload, path, expected_epoch)

    if path.name.startswith("runtime_epoch_"):
        return _validate_epoch_certificate(payload, path, expected_epoch)

    if path.name == "runtime_certificate.json":
        return _validate_generated_runtime_certificate(payload, expected_epoch)

    raise CertificateValidationError(
        "certificate does not match any supported runtime certificate schema"
    )


def _validate_legacy_certificate(
    payload: Mapping[str, Any],
    path: Path,
    expected_epoch: int | None,
) -> int:
    certificate_type = payload["certificate_type"]
    status = payload["status"]
    epoch = payload["epoch"]

    if certificate_type != "runtime_certificate":
        raise CertificateValidationError(
            f"invalid certificate_type: {certificate_type}"
        )

    if str(status).lower() not in {"valid", "passed"}:
        raise CertificateValidationError(f"invalid certificate status: {status}")

    epoch = _require_int(epoch, "certificate epoch")

    filename_epoch = _extract_epoch(path.name)

    if filename_epoch is not None and filename_epoch != epoch:
        raise CertificateValidationError(
            f"certificate epoch mismatch: filename={filename_epoch}, payload={epoch}"
        )

    _check_expected_epoch(epoch, expected_epoch)
    return epoch


def _validate_epoch_certificate(
    payload: Mapping[str, Any],
    path: Path,
    expected_epoch: int | None,
) -> int:
    filename_epoch = _extract_epoch(path.name)

    if filename_epoch is None:
        raise CertificateValidationError("epoch certificate filename has no epoch")

    payload_epoch = _find_epoch(payload)

    if payload_epoch is not None and payload_epoch != filename_epoch:
        raise CertificateValidationError(
            f"certificate epoch mismatch: filename={filename_epoch}, payload={payload_epoch}"
        )

    if not _has_any_proof_binding(payload):
        raise CertificateValidationError(
            "epoch certificate missing proof/hash/admission binding"
        )

    if _has_negative_status(payload):
        raise CertificateValidationError("epoch certificate contains failing status")

    _check_expected_epoch(filename_epoch, expected_epoch)
    return filename_epoch


def _validate_generated_runtime_certificate(
    payload: Mapping[str, Any],
    expected_epoch: int | None,
) -> int | None:
    if not payload:
        raise CertificateValidationError("runtime certificate payload is empty")

    epoch = _find_epoch(payload)

    if epoch is not None:
        epoch = _require_int(epoch, "runtime certificate epoch")

    if not _has_any_proof_binding(payload):
        raise CertificateValidationError(
            "runtime certificate missing proof/hash/admission binding"
        )

    if _has_negative_status(payload):
        raise CertificateValidationError("runtime certificate contains failing status")

    if expected_epoch is not None:
        _check_expected_epoch(epoch, expected_epoch)

    return epoch


def _check_expected_epoch(actual: int | None, expected: int | None) -> None:
    if expected is not None and actual != expected:
        raise CertificateValidationError(
            f"unexpected certificate epoch: expected={expected}, actual={actual}"
        )


def _require_int(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise CertificateValidationError(f"{label} must be an integer")

    if not isinstance(value, int):
        raise CertificateValidationError(f"{label} must be an integer")

    return value


def _has_any_proof_binding(payload: Mapping[str, Any]) -> bool:
    keys = _flatten_keys(payload)

    required_fragments = (
        "hash",
        "proof",
        "witness",
        "replay",
        "attestation",
        "admission",
        "signature",
        "certificate",
        "seal",
        "registry",
    )

    return any(fragment in key for key in keys for fragment in required_fragments)


def _has_negative_status(payload: Mapping[str, Any]) -> bool:
    bad_values = {
        "invalid",
        "failed",
        "failure",
        "rejected",
        "false",
        "error",
    }

    for value in _walk_values(payload):
        if isinstance(value, str) and value.strip().lower() in bad_values:
            return True

    return False


def _find_epoch(payload: Mapping[str, Any]) -> int | None:
    for key, value in _walk_items(payload):
        if key == "epoch":
            return _require_int(value, "certificate epoch")

    return None


def _flatten_keys(payload: Mapping[str, Any]) -> set[str]:
    return {key for key, _value in _walk_items(payload)}


def _walk_items(value: Any) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []

    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            items.append((key_text, child))
            items.extend(_walk_items(child))
    elif isinstance(value, list):
        for child in value:
            items.extend(_walk_items(child))

    return items


def _walk_values(value: Any) -> list[Any]:
    values: list[Any] = [value]

    if isinstance(value, Mapping):
        for child in value.values():
            values.extend(_walk_values(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk_values(child))

    return values


def _is_runtime_certificate_filename(filename: str) -> bool:
    return filename == "runtime_certificate.json" or filename.startswith(
        "runtime_epoch_"
    )


def _extract_epoch(filename: str) -> int | None:
    marker = "runtime_epoch_"

    if marker not in filename:
        return None

    suffix = filename.split(marker, 1)[1]
    digits: list[str] = []

    for char in suffix:
        if char.isdigit():
            digits.append(char)
        else:
            break

    if not digits:
        return None

    return int("".join(digits))


def main() -> int:
    try:
        default_path = find_default_certificate()
        result = validate_certificate(default_path)
    except CertificateValidationError as exc:
        print(f"❌ Certificate validation FAILED: {exc}")
        return 1

    print("✅ Certificate validation PASSED")
    print(f"✅ Certificate: {result.certificate_path}")
    print(f"✅ Epoch: {result.epoch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())