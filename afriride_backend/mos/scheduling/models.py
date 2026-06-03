import uuid

from django.db import models


class Journey(models.Model):
    STATUS_CHOICES = (
        ("planned", "Planned"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    journey_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user_id = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="planned")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Journey({self.journey_id}, {self.status})"


class JourneySegment(models.Model):
    SEGMENT_TYPES = (
        ("AFRIRIDE", "AfriRide"),
        ("BUS", "Bus"),
        ("TRAIN", "Train"),
        ("WALK", "Walk"),
        ("DELIVERY", "Delivery"),
    )

    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="segments",
    )
    segment_type = models.CharField(max_length=50, choices=SEGMENT_TYPES)
    sequence = models.IntegerField(default=0)
    start_location = models.JSONField()
    end_location = models.JSONField()
    evidence_reference = models.CharField(max_length=255, blank=True)
    replay_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("journey", "sequence")

    def __str__(self):
        return f"JourneySegment({self.segment_type}, {self.sequence})"
