"""
Django management entry point for the isolated AfriRide skeleton.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    """
    Run Django management commands when Django is installed.
    """

    # =====================================================
    # ✅ CRITICAL FIX — ADD PROJECT ROOT TO PYTHONPATH
    # =====================================================
    BASE_DIR = Path(__file__).resolve().parents[2]
    # This ensures Python can find `afritech` and other root modules
    sys.path.insert(0, str(BASE_DIR))

    # =====================================================
    # ✅ DJANGO SETTINGS MODULE
    # =====================================================
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "afriride_system.django_app.config.settings"
    )

    # =====================================================
    # ✅ SAFE DJANGO IMPORT
    # =====================================================
    try:
        from django.core.management import execute_from_command_line
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Django is required to run this management entry point"
        ) from exc

    # =====================================================
    # ✅ EXECUTION
    # =====================================================
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()