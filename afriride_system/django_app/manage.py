"""Django management entry point for the isolated AfriRide skeleton."""

from __future__ import annotations


def main() -> None:
    """Run Django management commands when Django is installed."""
    try:
        from django.core.management import execute_from_command_line
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency hook
        raise RuntimeError("Django is required to run this management entry point") from exc

    execute_from_command_line()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
