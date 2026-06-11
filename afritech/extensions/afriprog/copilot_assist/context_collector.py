from __future__ import annotations

from collections.abc import Mapping


def collect_context(
    *,
    target: str,
    files: Mapping[str, str] | None = None,
) -> dict[str, object]:
    file_payload = files or {}
    return {
        "target": target,
        "file_count": len(file_payload),
        "files": tuple(
            {
                "path": path,
                "line_count": len(content.splitlines()),
                "char_count": len(content),
            }
            for path, content in sorted(file_payload.items())
        ),
        "context_authority": "advisory_only",
        "mutates_runtime": False,
    }


__all__ = ["collect_context"]
