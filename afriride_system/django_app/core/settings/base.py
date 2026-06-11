"""Base settings for the isolated AfriRide Django skeleton."""

from __future__ import annotations
import os

SECRET_KEY = os.environ.get("AFRIRIDE_DJANGO_SECRET_KEY", "local-dev-only-not-for-production")
DEBUG = False
ROOT_URLCONF = "afriride_system.django_app.core.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "afriride_system.django_app.apps.ride_request",
    "afriride_system.django_app.apps.ride_lifecycle",
    "afriride_system.django_app.apps.pricing",
    "afriride_system.django_app.apps.ride_matching",
    "afriride_system.django_app.apps.rider",
    "afriride_system.django_app.apps.driver",
    "afriride_system.django_app.apps.safety",
    "afriride_system.django_app.apps.payments",
    "afriride_system.django_app.apps.notifications",
]

MIDDLEWARE = [
    "afriride_system.django_app.core.middleware.request_logging.RequestLoggingMiddleware",
    "afriride_system.django_app.core.middleware.auth_middleware.AuthMiddleware",
]
