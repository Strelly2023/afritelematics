from django.db import models


class FarePolicy(models.Model):
    """Deterministic fare policy used after replay-verified completion."""

    name = models.CharField(max_length=100, unique=True)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2)
    per_minute_rate = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
