from django.db import models
from django.utils import timezone
from evidence.models import EventLog


class Incident(models.Model):
    SEVERITY_CHOICES = (
        ("INFO", "Info"),
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    )

    region = models.ForeignKey("network.Region", on_delete=models.CASCADE)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Incident({self.severity}, {self.title})"


def open_incident(region, severity, title, description, actor=None):
    incident = Incident.objects.create(
        region=region,
        severity=severity,
        title=title,
        description=description,
    )

    EventLog.objects.create(
        event_type="network_incident_opened",
        actor=actor,
        metadata={
            "incident_id": incident.id,
            "region_id": region.id,
            "region_code": region.code,
            "severity": severity,
            "title": title,
        },
    )

    return incident


def resolve_incident(incident, actor=None):
    incident.resolved = True
    incident.resolved_at = timezone.now()
    incident.save(update_fields=["resolved", "resolved_at"])

    EventLog.objects.create(
        event_type="network_incident_resolved",
        actor=actor,
        metadata={
            "incident_id": incident.id,
            "region_id": incident.region_id,
            "severity": incident.severity,
        },
    )

    return incident
