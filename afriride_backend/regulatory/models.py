from django.db import models


class RegulatoryReport(models.Model):
    country = models.CharField(max_length=50)
    report_type = models.CharField(max_length=100)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    replay_verified = models.BooleanField(default=False)
    report_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"RegulatoryReport({self.country}, {self.report_type})"
