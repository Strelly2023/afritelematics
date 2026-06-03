from django.db import models


class IntelligenceRecommendation(models.Model):
    TYPE_CHOICES = (
        ("demand_prediction", "Demand Prediction"),
        ("surge_proposal", "Surge Proposal"),
        ("driver_positioning", "Driver Positioning"),
        ("dispatch_recommendation", "Dispatch Recommendation"),
    )

    recommendation_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    zone = models.ForeignKey(
        "zones.ServiceZone",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    ride = models.ForeignKey(
        "rides.Ride",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    payload = models.JSONField(default=dict)
    authority = models.CharField(max_length=50, default="recommendation_only")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"IntelligenceRecommendation({self.recommendation_type})"
