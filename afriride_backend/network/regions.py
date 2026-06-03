from django.db import models


class Region(models.Model):
    code = models.CharField(max_length=20, unique=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    launched_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("country", "city", "code")

    def __str__(self):
        return f"{self.code} - {self.city}, {self.country}"


class RegionOperator(models.Model):
    ROLE_CHOICES = (
        ("regional_manager", "Regional Manager"),
        ("operations_manager", "Operations Manager"),
        ("compliance_manager", "Compliance Manager"),
        ("support_manager", "Support Manager"),
    )

    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="operators")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("region", "user", "role")
        ordering = ("region", "role")

    def __str__(self):
        return f"{self.region_id}:{self.user_id}:{self.role}"


class FailoverPolicy(models.Model):
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="failover_policies",
    )
    backup_region = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("region", "backup_region")

    def __str__(self):
        return f"FailoverPolicy({self.region.code}->{self.backup_region})"


class ExpansionCandidate(models.Model):
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    readiness_score = models.FloatField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-readiness_score", "country", "city")

    def __str__(self):
        return f"{self.city}, {self.country}"
