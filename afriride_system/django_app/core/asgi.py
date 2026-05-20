"""ASGI entry point for the isolated AfriRide Django skeleton."""

from __future__ import annotations

try:
    from django.core.asgi import get_asgi_application
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    application = None
else:
    application = get_asgi_application()
