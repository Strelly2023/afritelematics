from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class SurfaceLocatorError(Exception):
    """Raised when surface detection fails."""


@dataclass(frozen=True)
class SurfaceMap:
    driver_app: tuple[str, ...]
    rider_app: tuple[str, ...]
    web_app: tuple[str, ...]
    backend: tuple[str, ...]
    unknown: tuple[str, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "driver_app": list(self.driver_app),
            "rider_app": list(self.rider_app),
            "web_app": list(self.web_app),
            "backend": list(self.backend),
            "unknown": list(self.unknown),
        }


class SurfaceLocator:
    """
    Deterministic repository surface classifier.

    Constitutional properties:
    - read-only
    - deterministic
    - classification only
    - non-authoritative
    """

    DRIVER_SURFACES = frozenset(
        {
            "driver_app",
            "driver",
        }
    )

    RIDER_SURFACES = frozenset(
        {
            "rider_app",
            "rider",
        }
    )

    WEB_SURFACES = frozenset(
        {
            "web_app",
            "web",
            "frontend",
        }
    )

    BACKEND_SURFACES = frozenset(
        {
            "afritech",
            "backend",
            "api",
            "services",
        }
    )

    def __init__(self, files: Iterable[str]):
        normalized = tuple(
            sorted(str(Path(file_path)) for file_path in files)
        )

        if any(not path for path in normalized):
            raise SurfaceLocatorError(
                "file paths must not be empty"
            )

        self.files = normalized

    def detect_surfaces(self) -> SurfaceMap:
        surfaces: dict[str, list[str]] = {
            "driver_app": [],
            "rider_app": [],
            "web_app": [],
            "backend": [],
            "unknown": [],
        }

        for file_path in self.files:
            classification = self._classify_surface(file_path)
            surfaces[classification].append(file_path)

        return SurfaceMap(
            driver_app=tuple(sorted(surfaces["driver_app"])),
            rider_app=tuple(sorted(surfaces["rider_app"])),
            web_app=tuple(sorted(surfaces["web_app"])),
            backend=tuple(sorted(surfaces["backend"])),
            unknown=tuple(sorted(surfaces["unknown"])),
        )

    def surface_counts(self) -> dict[str, int]:
        detected = self.detect_surfaces()

        return {
            "driver_app": len(detected.driver_app),
            "rider_app": len(detected.rider_app),
            "web_app": len(detected.web_app),
            "backend": len(detected.backend),
            "unknown": len(detected.unknown),
        }

    def canonical_dict(self) -> dict[str, object]:
        return {
            "file_count": len(self.files),
            "surface_counts": self.surface_counts(),
            "surfaces": self.detect_surfaces().canonical_dict(),
        }

    def _classify_surface(self, file_path: str) -> str:
        parts = set(Path(file_path).parts)

        if parts & self.DRIVER_SURFACES:
            return "driver_app"

        if parts & self.RIDER_SURFACES:
            return "rider_app"

        if parts & self.WEB_SURFACES:
            return "web_app"

        if parts & self.BACKEND_SURFACES:
            return "backend"

        return "unknown"