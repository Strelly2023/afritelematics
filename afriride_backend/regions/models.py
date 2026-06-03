from django.db import models


class RegionPolicy(models.Model):
    """Country-specific financial policy for replay-backed payments."""

    country_code = models.CharField(max_length=3, unique=True)
    currency = models.CharField(max_length=10)
    tax_name = models.CharField(max_length=20, default="VAT")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    default_payment_provider = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("country_code",)

    def __str__(self):
        return f"{self.country_code} ({self.currency})"
