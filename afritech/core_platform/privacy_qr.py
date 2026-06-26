"""Privacy-preserving QR envelope helpers for zk receipts."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import json
import zlib
from typing import Any, Mapping, Sequence

from afritech.core_platform.cryptographic_consensus import _canonicalize_seal, _hash
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.qr import render_qr_png
from afritech.core_platform.qr_proof import (
    MAX_QR_AGE_SECONDS,
    MAX_QR_DECOMPRESSED_BYTES,
    MAX_QR_PAYLOAD_BYTES,
    _parse_issued_at,
)
from afritech.core_platform.zk_receipts import build_zk_receipt_qr_bundle


def _stable_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )


def _canonical_privacy_qr_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    return _canonicalize_seal(
        {key: value for key, value in bundle.items() if key != "qr_hash"}
    )


def _privacy_qr_hash(bundle: Mapping[str, Any]) -> str:
    return _hash(_canonical_privacy_qr_bundle(bundle), domain=HASH_DOMAINS["ZK_QR_PAYLOAD"])


def build_privacy_qr_bundle(
    receipt: Mapping[str, Any],
    *,
    hidden_fields: Sequence[str] | None = None,
    chain_id: str | None = None,
    epoch: int | None = None,
    bridge: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_zk_receipt_qr_bundle(
        receipt,
        hidden_fields=hidden_fields,
        chain_id=chain_id,
        epoch=epoch,
        bridge=bridge,
    )
    return bundle


def encode_privacy_qr_payload(bundle: Mapping[str, Any]) -> str:
    if not isinstance(bundle, Mapping) or not bundle:
        raise ValueError("privacy_qr_bundle_required")
    wrapper = dict(bundle)
    wrapper["qr_hash"] = _privacy_qr_hash(wrapper)
    raw = _stable_json(_canonicalize_seal(wrapper))
    compressed = zlib.compress(raw.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("utf-8")


def build_privacy_qr_payload(
    receipt: Mapping[str, Any],
    *,
    hidden_fields: Sequence[str] | None = None,
    chain_id: str | None = None,
    epoch: int | None = None,
    bridge: Mapping[str, Any] | None = None,
) -> str:
    return encode_privacy_qr_payload(
        build_privacy_qr_bundle(
            receipt,
            hidden_fields=hidden_fields,
            chain_id=chain_id,
            epoch=epoch,
            bridge=bridge,
        )
    )


def decode_privacy_qr_payload(data: str) -> dict[str, Any]:
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
        raise ValueError("qr_invalid_payload")
    if payload.get("type") != "novatrust-zk-qr":
        raise ValueError("invalid_qr_type")

    qr_hash = payload.get("qr_hash")
    if not isinstance(qr_hash, str) or not qr_hash:
        raise ValueError("qr_invalid_hash")

    hash_input = {key: value for key, value in payload.items() if key != "qr_hash"}
    expected_hash = _privacy_qr_hash(hash_input)
    if qr_hash != expected_hash:
        raise ValueError("qr_integrity_failure")

    issued_at = payload.get("issued_at")
    if not isinstance(issued_at, str) or not issued_at.strip():
        raise ValueError("qr_missing_issued_at")
    parsed_issued_at = _parse_issued_at(issued_at)
    age_seconds = (datetime.now(timezone.utc) - parsed_issued_at).total_seconds()
    if age_seconds < 0:
        raise ValueError("qr_invalid_timestamp")
    if age_seconds > MAX_QR_AGE_SECONDS:
        raise ValueError("qr_expired")

    zk_receipt = payload.get("zk_receipt")
    if not isinstance(zk_receipt, Mapping) or not zk_receipt:
        raise ValueError("qr_missing_zk_receipt")
    bridge = payload.get("bridge")
    if bridge is not None and not isinstance(bridge, Mapping):
        raise ValueError("qr_invalid_bridge")

    return payload


def build_privacy_qr_artifact(
    receipt: Mapping[str, Any],
    *,
    hidden_fields: Sequence[str] | None = None,
    chain_id: str | None = None,
    epoch: int | None = None,
    bridge: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = build_privacy_qr_payload(
        receipt,
        hidden_fields=hidden_fields,
        chain_id=chain_id,
        epoch=epoch,
        bridge=bridge,
    )
    png = render_qr_png(payload, modules=29, scale=6)
    return {
        "qr_payload": payload,
        "qr_png": base64.b64encode(png).decode("ascii"),
        "qr_payload_bytes": len(payload.encode("utf-8")),
        "qr_png_bytes": len(png),
    }


__all__ = [
    "build_privacy_qr_artifact",
    "build_privacy_qr_bundle",
    "build_privacy_qr_payload",
    "decode_privacy_qr_payload",
    "encode_privacy_qr_payload",
]
