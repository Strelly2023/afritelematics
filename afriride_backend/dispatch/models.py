from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class DriverAvailability(models.Model):
    """Driver availability snapshot used by deterministic dispatch.

    This is input to backend dispatch. It is not proof of ride truth by itself.
    """

    driver = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="availability",
    )
    is_available = models.BooleanField(default=False)
    current_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    current_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("updated_at", "id")

    def __str__(self) -> str:
        return f"DriverAvailability(driver={self.driver_id}, available={self.is_available})"
