from django.db import models


class PilotProgram(models.Model):
    STATUS_CHOICES = (
        ("pilot_ready", "Pilot Ready"),
        ("pilot_executed", "Pilot Executed"),
        ("pilot_verified", "Pilot Verified"),
        ("pilot_certified", "Pilot Certified"),
        ("pilot_failed", "Pilot Failed"),
    )

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pilot_ready",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} ({self.city})"


class PilotParticipant(models.Model):
    ROLE_CHOICES = (
        ("rider", "Rider"),
        ("driver", "Driver"),
        ("operator", "Operator"),
        ("observer", "Observer"),
        ("auditor", "Auditor"),
    )

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    pilot = models.ForeignKey(
        PilotProgram,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "pilot", "role")
        ordering = ("pilot", "role")

    def __str__(self):
        return f"{self.pilot_id}:{self.user_id}:{self.role}"


class PilotEvidence(models.Model):
    pilot = models.ForeignKey(
        PilotProgram,
        on_delete=models.CASCADE,
        related_name="evidence_records",
    )
    ride = models.ForeignKey("rides.Ride", on_delete=models.CASCADE)
    replay_verified = models.BooleanField()
    receipt_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("pilot", "ride")
        ordering = ("-created_at",)

    def __str__(self):
        return f"PilotEvidence(pilot={self.pilot_id}, ride={self.ride_id})"


class PilotMetrics(models.Model):
    pilot = models.OneToOneField(
        PilotProgram,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    total_rides = models.IntegerField(default=0)
    completed_rides = models.IntegerField(default=0)
    replay_verified_rides = models.IntegerField(default=0)
    fraud_flags = models.IntegerField(default=0)
    payment_success_rate = models.FloatField(default=0)
    service_availability = models.FloatField(default=0)
    driver_utilization = models.FloatField(default=0)
    driver_satisfaction = models.FloatField(default=0)
    rider_satisfaction = models.FloatField(default=0)
    driver_satisfaction_target = models.FloatField(default=80)
    rider_satisfaction_target = models.FloatField(default=80)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PilotMetrics(pilot={self.pilot_id})"


class PilotCertificate(models.Model):
    pilot = models.OneToOneField(
        PilotProgram,
        on_delete=models.CASCADE,
        related_name="certificate",
    )
    ride_count = models.IntegerField()
    replay_verification_rate = models.FloatField()
    payment_success_rate = models.FloatField(default=0)
    fraud_flags = models.IntegerField(default=0)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-issued_at",)

    def __str__(self):
        return f"PilotCertificate(pilot={self.pilot_id})"
