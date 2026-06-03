from __future__ import annotations

from pathlib import Path


ALLOWED_ROOTS = (
    "afritech/extensions",
)


class SandboxError(Exception):
    """Raised when sandbox validation fails."""


def normalize_path(path: str | Path) -> str:
    """
    Deterministically normalize a repository-relative path.
    """

    return Path(path).as_posix()


def is_authorized_path(path: str | Path) -> bool:
    """
    Read-only authorization check.
    """

    normalized = normalize_path(path)

    return any(
        normalized == root or normalized.startswith(f"{root}/")
        for root in ALLOWED_ROOTS
    )


def validate_path(path: str | Path) -> str:
    """
    Validate repository-relative path access.

    Constitutional properties:
    - deterministic
    - read-only
    - traversal resistant
    - non-authoritative
    """

    normalized = normalize_path(path)

    if not normalized:
        raise SandboxError("path must not be empty")

    parts = Path(normalized).parts

    if ".." in parts:
        raise SandboxError(
            f"path traversal detected: {path}"
        )

    if normalized.startswith("/"):
        raise SandboxError(
            f"absolute paths are not permitted: {path}"
        )

    if not is_authorized_path(normalized):
        raise SandboxError(
            f"unauthorized path: {path}"
        )

    return normalized


def validate_paths(
    paths: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    """
    Validate multiple paths deterministically.
    """

    return tuple(
        sorted(
            validate_path(path)
            for path in paths
        )
    )


def sandbox_receipt(
    path: str | Path,
) -> dict[str, object]:
    """
    Evidence-ready validation receipt.
    """

    normalized = validate_path(path)

    return {
        "path": normalized,
        "authorized": True,
        "allowed_roots": list(ALLOWED_ROOTS),
    }
