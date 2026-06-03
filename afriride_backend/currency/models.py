from django.db import models


class CurrencyRate(models.Model):
    """Declared exchange rate for controlled test conversion.

    Production currency conversion requires provider-backed rate provenance and
    certification. This model is a scaffold for policy-controlled conversion.
    """

    source_currency = models.CharField(max_length=10)
    target_currency = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    active = models.BooleanField(default=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("source_currency", "target_currency", "active")
        ordering = ("source_currency", "target_currency")

    def __str__(self):
        return f"{self.source_currency}->{self.target_currency}"
