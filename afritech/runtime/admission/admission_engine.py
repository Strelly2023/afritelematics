"""Runtime admission engine for constitutional execution.

This module is the canonical admission surface for AfriTech runtime boot.

It exists to enforce the rule:

    no runtime execution exists without constitutional admission

The CI admission rule targets this file explicitly and requires runtime
entrypoints to import RuntimeAdmissionEngine and call admit() before any
execution path is reachable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class RuntimeAdmissionError(RuntimeError):
    """Raised when runtime admission fails."""


@dataclass(frozen=True)
class RuntimeAdmissionDecision:
    """Deterministic admission result."""

    admitted: bool
    reason: str
    certificate_path: str
    epoch: int | None = None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
            "certificate_path": self.certificate_path,
            "epoch": self.epoch,
        }


class RuntimeAdmissionEngine:
    """Fail-closed runtime admission engine.

    This engine does not execute runtime work.
    It only decides whether the runtime may become reachable.
    """

    def __init__(
        self,
        certificate_path: str | Path,
        *,
        expected_epoch: int | None = None,
    ) -> None:
        self.certificate_path = Path(certificate_path)
        self.expected_epoch = expected_epoch

    def admit(self) -> RuntimeAdmissionDecision:
        """Admit runtime only if the runtime certificate is present and valid."""

        if not self.certificate_path.exists():
            raise RuntimeAdmissionError(
                f"runtime admission failed: certificate not found: "
                f"{self.certificate_path}"
            )

        if not self.certificate_path.is_file():
            raise RuntimeAdmissionError(
                f"runtime admission failed: certificate path is not a file: "
                f"{self.certificate_path}"
            )

        if "runtime_epoch_" not in self.certificate_path.name:
            raise RuntimeAdmissionError(
                "runtime admission failed: certificate filename must contain "
                "'runtime_epoch_'"
            )

        epoch = self._extract_epoch(self.certificate_path.name)

        if self.expected_epoch is not None and epoch != self.expected_epoch:
            raise RuntimeAdmissionError(
                f"runtime admission failed: epoch mismatch "
                f"(expected={self.expected_epoch}, actual={epoch})"
            )

        return RuntimeAdmissionDecision(
            admitted=True,
            reason="runtime_admitted",
            certificate_path=str(self.certificate_path),
            epoch=epoch,
        )

    @staticmethod
    def _extract_epoch(filename: str) -> int | None:
        marker = "runtime_epoch_"

        if marker not in filename:
            return None

        suffix = filename.split(marker, 1)[1]
        digits = []

        for char in suffix:
            if char.isdigit():
                digits.append(char)
            else:
                break

        if not digits:
            return None

        return int("".join(digits))


def require_runtime_admission(
    certificate_path: str | Path,
    *,
    expected_epoch: int | None = None,
) -> RuntimeAdmissionDecision:
    """Convenience fail-closed admission helper."""

    return RuntimeAdmissionEngine(
        certificate_path,
        expected_epoch=expected_epoch,
    ).admit()