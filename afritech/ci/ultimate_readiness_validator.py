from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def validate() -> bool:
    required_files = (
        ROOT / "afritech/federation/discovery.py",
        ROOT / "afritech/interoperability/external_proofs.py",
        ROOT / "afritech/legal/evidence.py",
        ROOT / "afritech/pilot/activation.py",
        ROOT / "afritech/tests/federation/test_discovery.py",
        ROOT / "afritech/tests/interoperability/test_external_proofs.py",
        ROOT / "afritech/tests/legal/test_evidence.py",
        ROOT / "afritech/tests/pilot/test_activation.py",
    )
    for path in required_files:
        if not path.exists():
            raise SystemExit(f"missing ultimate readiness file: {path}")

    _require(
        (ROOT / "afritech/federation/discovery.py").read_text(encoding="utf-8"),
        ("NodeAnnouncement", "signature", "verified=True"),
    )
    _require(
        (ROOT / "afritech/interoperability/external_proofs.py").read_text(encoding="utf-8"),
        ('"independently_verified": False', "verify_external_proof_reference"),
    )
    _require(
        (ROOT / "afritech/legal/evidence.py").read_text(encoding="utf-8"),
        ("projection_hash", "valid_witnesses", "stored_event_signature_verified"),
    )
    _require(
        (ROOT / "afritech/pilot/activation.py").read_text(encoding="utf-8"),
        ("READY_BLOCKED", "economic_activation_requested", "collect real-world pilot evidence only"),
    )
    return True


def _require(source: str, needles: tuple[str, ...]) -> None:
    compact_source = source.replace(" ", "")
    for needle in needles:
        if needle not in source and needle.replace(" ", "") not in compact_source:
            raise SystemExit(f"missing readiness invariant: {needle}")


def main() -> int:
    validate()
    print("ULTIMATE_READINESS_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
