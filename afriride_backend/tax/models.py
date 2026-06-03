from django.db import models


class TaxRecord(models.Model):
    """Stored tax calculation record for financial evidence."""

    ride = models.OneToOneField("rides.Ride", on_delete=models.CASCADE)
    country_code = models.CharField(max_length=3)
    tax_name = models.CharField(max_length=20)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"TaxRecord(ride={self.ride_id}, {self.country_code})"
