"""Django app config for AfriPay."""

from __future__ import annotations

from django.apps import AppConfig


class AfriPayConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "afriride_system.django_app.apps.afripay"
    label = "afripay"
