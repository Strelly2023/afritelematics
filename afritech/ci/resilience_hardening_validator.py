from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def validate() -> bool:
    required_files = (
        ROOT / "afritech/federation/resilience.py",
        ROOT / "afritech/afripower/resilience_intelligence.py",
        ROOT / "afritech/tests/federation/test_resilience.py",
        ROOT / "afritech/tests/afripower/test_resilience_intelligence.py",
    )
    for path in required_files:
        if not path.exists():
            raise SystemExit(f"missing resilience hardening file: {path}")

    _require(
        (ROOT / "afritech/federation/protocol.py").read_text(encoding="utf-8"),
        ("MAX_CLOCK_SKEW_SECONDS = 30", "MESSAGE_EXPIRY_SECONDS = 60"),
    )
    _require(
        (ROOT / "afritech/federation/resilience.py").read_text(encoding="utf-8"),
        (
            "CONSENSUS_UNRESOLVED",
            "CONSENSUS_NO_AGREEMENT",
            "finality_halted=True",
            "record_replay_divergence",
            "is_isolated",
        ),
    )
    _require(
        (ROOT / "afritech/afripower/resilience_intelligence.py").read_text(encoding="utf-8"),
        ("advisory_only", "execution_authority", "suggest_quorum_posture"),
    )
    return True


def _require(source: str, needles: tuple[str, ...]) -> None:
    compact_source = source.replace(" ", "")
    for needle in needles:
        if needle not in source and needle.replace(" ", "") not in compact_source:
            raise SystemExit(f"missing resilience invariant: {needle}")


def main() -> int:
    validate()
    print("RESILIENCE_HARDENING_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
