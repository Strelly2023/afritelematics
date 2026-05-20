"""WSGI entry point for the isolated AfriRide Django skeleton."""

from __future__ import annotations

try:
    from django.core.wsgi import get_wsgi_application
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    application = None
else:
    application = get_wsgi_application()
