"""CLI entrypoint for CI impact analysis."""

from __future__ import annotations

from .change_impact_analyzer import main


if __name__ == "__main__":
    raise SystemExit(main())
