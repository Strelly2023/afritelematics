from __future__ import annotations

from pathlib import Path
from typing import Any

from afritech.extensions.afriprog.code_executor.sandbox import (
    SandboxError,
    validate_path,
)


class SafeWriteDisabledError(Exception):
    """
    Raised when a write operation is attempted while the
    write surface is constitutionally disabled.
    """


PHASE = "PHASE_3_PROPOSAL_ONLY"
WRITE_ENABLED = False


def safe_write(
    path: str | Path,
    content: str,
    *,
    create_parents: bool = False,
) -> None:
    """
    Constitutional write barrier.

    Phase 3 rules:
    - writes forbidden
    - patch proposals allowed
    - receipts allowed
    - file mutation forbidden
    """

    try:
        validate_path(path)
    except SandboxError as exc:
        raise SafeWriteDisabledError(
            f"Sandbox validation failed: {exc}"
        ) from exc

    raise SafeWriteDisabledError(
        "Write operations are disabled in "
        f"{PHASE} (proposal-only mode)"
    )


def safe_append(
    path: str | Path,
    content: str,
) -> None:
    """
    Append barrier.
    """

    safe_write(path, content)


def safe_delete(
    path: str | Path,
) -> None:
    """
    Delete barrier.
    """

    try:
        validate_path(path)
    except SandboxError as exc:
        raise SafeWriteDisabledError(
            f"Sandbox validation failed: {exc}"
        ) from exc

    raise SafeWriteDisabledError(
        "Delete operations are disabled in "
        f"{PHASE} (proposal-only mode)"
    )


def safe_rename(
    source: str | Path,
    destination: str | Path,
) -> None:
    """
    Rename barrier.
    """

    try:
        validate_path(source)
        validate_path(destination)
    except SandboxError as exc:
        raise SafeWriteDisabledError(
            f"Sandbox validation failed: {exc}"
        ) from exc

    raise SafeWriteDisabledError(
        "Rename operations are disabled in "
        f"{PHASE} (proposal-only mode)"
    )


def write_status() -> dict[str, Any]:
    """
    Evidence-ready status receipt.
    """

    return {
        "phase": PHASE,
        "write_enabled": WRITE_ENABLED,
        "append_enabled": False,
        "delete_enabled": False,
        "rename_enabled": False,
        "status": "proposal_only",
    }