from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class FailureParserError(Exception):
    """Raised when failure parsing fails."""


@dataclass(frozen=True)
class FailureSignal:
    signal: str
    confidence: float
    evidence: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "signal": self.signal,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


class FailureParser:
    """
    Deterministic validator/test failure parser.

    Constitutional properties:
    - read-only
    - deterministic
    - inference only
    - non-authoritative
    """

    SIGNAL_RULES = {
        "missing_element": (
            "not found",
            "cannot import",
            "no module named",
            "missing",
            "undefined",
        ),
        "assertion_failure": (
            "assert",
            "assertionerror",
            "expected",
            "!= ",
        ),
        "runtime_error": (
            "exception",
            "traceback",
            "runtimeerror",
            "typeerror",
            "valueerror",
            "attributeerror",
            "keyerror",
        ),
        "syntax_error": (
            "syntaxerror",
            "invalid syntax",
            "indentationerror",
        ),
        "import_error": (
            "importerror",
            "cannot import",
            "module not found",
        ),
        "validation_failure": (
            "validation failed",
            "validator failed",
            "ci failed",
        ),
    }

    def __init__(self, failure_text: str):
        if not isinstance(failure_text, str):
            raise FailureParserError(
                "failure_text must be a string"
            )

        self.failure_text = failure_text
        self.normalized_text = failure_text.lower()

    def extract_signals(self) -> tuple[FailureSignal, ...]:
        discovered: list[FailureSignal] = []

        for signal_name, patterns in sorted(
            self.SIGNAL_RULES.items()
        ):
            matched_pattern = self._find_match(patterns)

            if matched_pattern is None:
                continue

            discovered.append(
                FailureSignal(
                    signal=signal_name,
                    confidence=1.0,
                    evidence=matched_pattern,
                )
            )

        return tuple(
            sorted(
                discovered,
                key=lambda item: item.signal,
            )
        )

    def signal_names(self) -> tuple[str, ...]:
        return tuple(
            signal.signal
            for signal in self.extract_signals()
        )

    def has_failures(self) -> bool:
        return bool(self.extract_signals())

    def canonical_dict(self) -> dict[str, object]:
        return {
            "signal_count": len(
                self.extract_signals()
            ),
            "signals": [
                signal.canonical_dict()
                for signal in self.extract_signals()
            ],
        }

    def _find_match(
        self,
        patterns: Iterable[str],
    ) -> str | None:
        for pattern in patterns:
            if pattern in self.normalized_text:
                return pattern

        return None