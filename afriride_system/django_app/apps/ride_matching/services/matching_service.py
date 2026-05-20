"""Deterministic driver assignment skeleton."""

from __future__ import annotations

from afriride_system.django_app.apps.driver.models import Driver


class MatchingService:
    """Assign the first available driver in stable insertion order."""

    @staticmethod
    def assign_driver() -> Driver | None:
        return Driver.objects.filter(is_available=True).first()
