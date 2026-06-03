from django.db import models


class PublicTransportProvider(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("country", "city", "name")

    def __str__(self):
        return f"{self.name} ({self.provider_type})"


class PublicTransportStop(models.Model):
    provider = models.ForeignKey(
        PublicTransportProvider,
        on_delete=models.CASCADE,
        related_name="stops",
    )
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    external_id = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("provider", "name")

    def __str__(self):
        return self.name
