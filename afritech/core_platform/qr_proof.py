"""QR proof encoding for portable NovaTrust receipts."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import json
import zlib
from typing import Any, Mapping

from afritech.core_platform.cryptographic_consensus import _canonicalize_seal, _hash
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.qr import render_qr_png


MAX_QR_PAYLOAD_BYTES = 50_000
MAX_QR_DECOMPRESSED_BYTES = 250_000
MAX_QR_AGE_SECONDS = 60 * 60 * 24


def _stable_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )


def _canonical_qr_wrapper(wrapper: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": str(wrapper.get("type", "")).strip(),
        "version": str(wrapper.get("version", "")).strip(),
        "receipt": _canonicalize_seal(wrapper.get("receipt", {})),
    }


def _qr_hash(wrapper: Mapping[str, Any]) -> str:
    return _hash(_canonical_qr_wrapper(wrapper), domain=HASH_DOMAINS["QR_PAYLOAD"])


def _parse_issued_at(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("qr_invalid_timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError("qr_invalid_timestamp")
    if parsed.tzinfo is None:
        raise ValueError("qr_timestamp_missing_timezone")
    return parsed.astimezone(timezone.utc)


def encode_qr_payload(receipt: Mapping[str, Any]) -> str:
    if not isinstance(receipt, Mapping) or not receipt:
        raise ValueError("receipt_required")
    wrapper = {
        "type": "novatrust-qr-proof",
        "version": "1.0",
        "receipt": receipt,
    }
    wrapper["qr_hash"] = _qr_hash(wrapper)
    raw = _stable_json(wrapper)
    compressed = zlib.compress(raw.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("utf-8")


def decode_qr_payload(data: str) -> dict[str, Any]:
    if not isinstance(data, str) or not data.strip():
        raise ValueError("qr_payload_required")
    if len(data.encode("utf-8")) > MAX_QR_PAYLOAD_BYTES:
        raise ValueError("qr_payload_too_large")
    try:
        compressed = base64.b64decode(
            data.encode("utf-8"),
            altchars=b"-_",
            validate=True,
        )
    except binascii.Error as exc:
        raise ValueError("qr_invalid_base64") from exc
    try:
        decompressor = zlib.decompressobj()
        raw_bytes = decompressor.decompress(
            compressed,
            MAX_QR_DECOMPRESSED_BYTES + 1,
        )
        if len(raw_bytes) > MAX_QR_DECOMPRESSED_BYTES:
            raise ValueError("qr_decompressed_too_large")
        if decompressor.unconsumed_tail or decompressor.unused_data:
            raise ValueError("qr_decompressed_too_large")
        if not decompressor.eof:
            raise ValueError("qr_truncated_compression")
    except zlib.error as exc:
        raise ValueError("qr_invalid_compression") from exc
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("qr_invalid_encoding") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("qr_invalid_json") from exc
    if not isinstance(payload, dict):
        raise ValueError("qr_payload_must_be_object")
    if payload.get("type") != "novatrust-qr-proof":
        raise ValueError("invalid_qr_type")
    receipt = payload.get("receipt")
    if not isinstance(receipt, dict) or not receipt:
        raise ValueError("qr_receipt_required")
    qr_hash = payload.get("qr_hash")
    if not isinstance(qr_hash, str) or not qr_hash:
        raise ValueError("qr_invalid_hash")
    hash_input = {key: value for key, value in payload.items() if key != "qr_hash"}
    expected_hash = _qr_hash(hash_input)
    if qr_hash != expected_hash:
        raise ValueError("qr_integrity_failure")
    if not receipt.get("issued_at"):
        raise ValueError("qr_missing_issued_at")
    issued_at = _parse_issued_at(receipt["issued_at"])
    now = datetime.now(timezone.utc)
    age_seconds = (now - issued_at).total_seconds()
    if age_seconds < 0:
        raise ValueError("qr_invalid_timestamp")
    if age_seconds > MAX_QR_AGE_SECONDS:
        raise ValueError("qr_expired")
    return receipt


def build_qr_png(receipt: Mapping[str, Any]) -> bytes:
    return render_qr_png(encode_qr_payload(receipt), modules=29, scale=6)


def build_qr_artifact(receipt: Mapping[str, Any]) -> dict[str, Any]:
    payload = encode_qr_payload(receipt)
    png = build_qr_png(receipt)
    return {
        "qr_payload": payload,
        "qr_png": base64.b64encode(png).decode("ascii"),
        "qr_png_bytes": len(png),
    }


__all__ = [
    "MAX_QR_DECOMPRESSED_BYTES",
    "MAX_QR_PAYLOAD_BYTES",
    "MAX_QR_AGE_SECONDS",
    "build_qr_artifact",
    "build_qr_png",
    "decode_qr_payload",
    "encode_qr_payload",
]
