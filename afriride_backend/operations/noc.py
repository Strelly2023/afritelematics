from django.db import models


class NetworkHealthSnapshot(models.Model):
    region = models.ForeignKey("network.Region", on_delete=models.CASCADE)
    active_rides = models.IntegerField()
    replay_success_rate = models.FloatField()
    payment_success_rate = models.FloatField()
    uptime = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"NetworkHealthSnapshot(region={self.region_id})"
