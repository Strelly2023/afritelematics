from django.db import models


class LocationEvidence(models.Model):
    """Immutable GPS evidence point for a ride.

    This model records observed location facts. It does not decide ride truth
    and must be interpreted by route replay and canonical ride EventLog.
    """

    ride = models.ForeignKey(
        "rides.Ride",
        on_delete=models.CASCADE,
        related_name="gps_points",
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    speed = models.FloatField(default=0)
    heading = models.FloatField(default=0)
    recorded_at = models.DateTimeField()
    previous_hash = models.CharField(max_length=64, blank=True, default="")
    event_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("recorded_at", "id")
        indexes = [
            models.Index(fields=("ride", "recorded_at")),
            models.Index(fields=("ride", "event_hash")),
        ]

    def __str__(self):
        return f"LocationEvidence(ride={self.ride_id}, recorded_at={self.recorded_at})"
