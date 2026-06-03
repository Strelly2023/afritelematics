"""
afritech.ci.distributed_transcript_validator

CI validator for AfriTech distributed execution transcripts.

This validator enforces that distributed execution transcripts are:
- deterministic
- hash-bound
- replay-safe
- partition ordered
- closed-world aligned
- free from duplicate execution identities

Constitutional boundary:
- Transcript validation checks evidence admissibility.
- It does not define execution truth.
- Replay remains the truth authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import json

from afritech.distributed.replay.distributed_execution_transcript import (
    DistributedExecutionTranscript,
    DistributedExecutionTranscriptError,
    require_valid_distributed_execution_transcript,
    verify_distributed_execution_transcript,
    transcript_from_mappings,
)


# ============================================================
# ERROR
# ============================================================

class DistributedTranscriptValidatorError(ValueError):
    """Raised when distributed transcript validation fails."""


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class DistributedTranscriptValidationResult:
    passed: bool
    checked_transcripts: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed transcript validation PASSED\n"
                f"✅ Checked transcripts: {self.checked_transcripts}"
            )

        return (
            "❌ Distributed transcript validation FAILED\n"
            f"❌ Checked transcripts: {self.checked_transcripts}\n"
            + "\n".join(self.failures)
        )


# ============================================================
# CORE VALIDATION
# ============================================================

def validate_transcript(
    transcript: DistributedExecutionTranscript,
) -> None:
    """
    Validate one distributed execution transcript.

    Raises on failure.
    """

    # ✅ structural validation
    try:
        require_valid_distributed_execution_transcript(transcript)
    except DistributedExecutionTranscriptError as exc:
        raise DistributedTranscriptValidatorError(str(exc)) from exc

    # ✅ semantic + integrity validation
    verification = verify_distributed_execution_transcript(transcript)

    if not verification.valid:
        raise DistributedTranscriptValidatorError(
            "transcript verification failed: "
            + ", ".join(verification.reasons)
        )


def validate_transcript_mappings(
    mappings: list[dict[str, object]],
) -> None:
    """
    Validate transcript entries represented as mapping dictionaries.
    """

    try:
        transcript = transcript_from_mappings(
            transcript_id=None,  # ✅ FIX: required param
            entries=mappings,
        )

        validate_transcript(transcript)

    except DistributedExecutionTranscriptError as exc:
        raise DistributedTranscriptValidatorError(str(exc)) from exc


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_transcript_file(path: Path) -> None:
    """
    Validate a JSON transcript file.
    """

    if not path.exists():
        raise DistributedTranscriptValidatorError(f"missing transcript file: {path}")

    if path.suffix != ".json":
        raise DistributedTranscriptValidatorError(
            f"transcript file must be JSON: {path}"
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DistributedTranscriptValidatorError(
            f"failed to parse transcript JSON: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise DistributedTranscriptValidatorError(
            f"transcript file must contain object root: {path}"
        )

    entries = data.get("entries")

    if not isinstance(entries, list):
        raise DistributedTranscriptValidatorError(
            f"transcript file missing entries list: {path}"
        )

    if not entries:
        raise DistributedTranscriptValidatorError(
            f"transcript file contains empty entries list: {path}"
        )

    for entry in entries:
        if not isinstance(entry, dict):
            raise DistributedTranscriptValidatorError(
                f"transcript entry must be object: {path}"
            )

    validate_transcript_mappings(entries)


# ============================================================
# DIRECTORY VALIDATION
# ============================================================

def validate_transcript_directory(
    directory: Path,
) -> DistributedTranscriptValidationResult:
    """
    Validate all JSON distributed transcript files in a directory.
    """

    if not directory.exists():
        return DistributedTranscriptValidationResult(
            passed=True,
            checked_transcripts=0,
            failures=(),
        )

    if not directory.is_dir():
        raise DistributedTranscriptValidatorError(
            f"transcript path is not a directory: {directory}"
        )

    failures: list[str] = []
    checked = 0

    for path in sorted(directory.glob("*.json")):
        checked += 1

        try:
            validate_transcript_file(path)
        except DistributedTranscriptValidatorError as exc:
            failures.append(f"{path}: {exc}")

    return DistributedTranscriptValidationResult(
        passed=not failures,
        checked_transcripts=checked,
        failures=tuple(failures),
    )


# ============================================================
# ENTRYPOINT
# ============================================================

def validate_distributed_transcripts() -> DistributedTranscriptValidationResult:
    """
    Validate known distributed transcript evidence directories.
    """

    transcript_dir = Path("afritech/distributed/replay/transcripts")

    return validate_transcript_directory(transcript_dir)


def main() -> int:
    """
    CLI entrypoint.

    Usage:
        python3 -m afritech.ci.distributed_transcript_validator
    """

    try:
        result = validate_distributed_transcripts()
    except DistributedTranscriptValidatorError as exc:
        print("❌ Distributed transcript validation FAILED")
        print(str(exc))
        return 1

    print(result.report())

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())