from django.db import models


class Payment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    ride = models.OneToOneField("rides.Ride", on_delete=models.CASCADE)
    rider = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="AUD")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    provider = models.CharField(max_length=50, default="mock")
    provider_reference = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=3, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Payment(ride={self.ride_id}, status={self.status})"
