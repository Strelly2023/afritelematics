from django.db import models


class GovernmentPartner(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=50)
    endpoint_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("country", "name")

    def __str__(self):
        return f"{self.name} ({self.country})"


class GovernmentSubmission(models.Model):
    partner = models.ForeignKey(GovernmentPartner, on_delete=models.CASCADE)
    report = models.ForeignKey("regulatory.RegulatoryReport", on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="pending")
    submitted_at = models.DateTimeField(null=True, blank=True)
    submission_reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"GovernmentSubmission({self.partner_id}, {self.status})"
