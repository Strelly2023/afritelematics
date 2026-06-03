from django.db import models


class BillingAccount(models.Model):
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fleet = models.OneToOneField(
        "fleets.Fleet",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    country = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("country", "currency")

    def __str__(self):
        target = self.organization_id or self.fleet_id
        return f"BillingAccount({target}, {self.currency})"


class BusinessRideCharge(models.Model):
    billing_account = models.ForeignKey(BillingAccount, on_delete=models.CASCADE)
    ride = models.OneToOneField("rides.Ride", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    replay_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"BusinessRideCharge(ride={self.ride_id}, amount={self.amount})"
