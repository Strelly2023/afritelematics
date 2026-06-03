import uuid

from django.db import models


class ProductionReadinessCertificate(models.Model):
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    pilot_id = models.IntegerField()
    readiness_score = models.FloatField()
    certified = models.BooleanField(default=False)
    replay_verified = models.BooleanField(default=False)
    validation_summary = models.JSONField(default=dict)

    class Meta:
        ordering = ("-issued_at",)

    def __str__(self):
        return f"ProductionReadinessCertificate({self.certificate_id})"
