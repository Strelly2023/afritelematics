from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SurfaceDecision:
    admitted: bool
    reason: str
    violations: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
            "violations": list(self.violations),
        }


class SurfaceGuard:
    """
    AfriProgramming surface containment guard.

    Allows AfriProgramming activity only on approved extension surfaces.
    """

    ALLOWED_ROOTS = frozenset(
        {
            "afritech/extensions/afriprog",
        }
    )

    FORBIDDEN_ROOTS = frozenset(
        {
            "afritech/constitution",
            "afritech/guards",
            "afritech/ci",
            "afritech/registry",
            "afritech/runtime",
            "ecosystems/afriride",
            "ecosystems/afriprogramming",
        }
    )

    def evaluate_paths(
        self,
        paths: tuple[str, ...] | list[str],
    ) -> SurfaceDecision:
        violations: list[str] = []

        for raw_path in paths:
            path = Path(raw_path).as_posix()

            if path.startswith("/"):
                violations.append(f"absolute_path:{path}")
                continue

            if ".." in Path(path).parts:
                violations.append(f"path_traversal:{path}")
                continue

            if any(path.startswith(root) for root in self.FORBIDDEN_ROOTS):
                violations.append(f"forbidden_surface:{path}")
                continue

            if not any(path.startswith(root) for root in self.ALLOWED_ROOTS):
                violations.append(f"unauthorized_surface:{path}")

        if violations:
            return SurfaceDecision(
                admitted=False,
                reason="surface_violation",
                violations=tuple(sorted(violations)),
            )

        return SurfaceDecision(
            admitted=True,
            reason="surface_admitted",
            violations=(),
        )

    def evaluate_payload(self, payload: dict[str, Any]) -> SurfaceDecision:
        paths = tuple(
            str(item)
            for item in payload.get("paths", ())
        )

        return self.evaluate_paths(paths)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "guard": "SurfaceGuard",
            "allowed_roots": sorted(self.ALLOWED_ROOTS),
            "forbidden_roots": sorted(self.FORBIDDEN_ROOTS),
        }