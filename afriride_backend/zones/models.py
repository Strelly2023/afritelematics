from django.db import models


class ServiceZone(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "city", "country")
        ordering = ("country", "city", "name")

    def __str__(self):
        return f"{self.name}, {self.city}"


class ZoneDemandSnapshot(models.Model):
    zone = models.ForeignKey(
        ServiceZone,
        on_delete=models.CASCADE,
        related_name="demand_snapshots",
    )
    active_rides = models.IntegerField(default=0)
    available_drivers = models.IntegerField(default=0)
    predicted_demand = models.IntegerField(default=0)
    surge_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
    )
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-captured_at",)

    def __str__(self):
        return f"ZoneDemandSnapshot(zone={self.zone_id}, demand={self.predicted_demand})"
