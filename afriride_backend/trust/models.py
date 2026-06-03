from django.db import models


class TrustProfile(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    score = models.IntegerField(default=100)
    completed_rides = models.IntegerField(default=0)
    cancelled_rides = models.IntegerField(default=0)
    fraud_flags = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user_id",)

    def __str__(self):
        return f"TrustProfile(user={self.user_id}, score={self.score})"


class TrustEvent(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    ride = models.ForeignKey(
        "rides.Ride",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=50)
    score_delta = models.IntegerField(default=0)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"TrustEvent(user={self.user_id}, type={self.event_type})"
