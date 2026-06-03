from django.db import models


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    max_users = models.IntegerField(default=1)
    max_vehicles = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("monthly_price", "name")

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fleet = models.ForeignKey(
        "fleets.Fleet",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-started_at",)

    def __str__(self):
        target = self.organization_id or self.fleet_id
        return f"Subscription({target}, {self.status})"
