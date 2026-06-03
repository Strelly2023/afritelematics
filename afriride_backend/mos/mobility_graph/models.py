import uuid

from django.db import models


class MobilityNode(models.Model):
    NODE_TYPES = (
        ("driver", "Driver"),
        ("vehicle", "Vehicle"),
        ("rider", "Rider"),
        ("fleet", "Fleet"),
        ("bus", "Bus"),
        ("train", "Train"),
        ("station", "Station"),
        ("depot", "Depot"),
        ("warehouse", "Warehouse"),
        ("hospital", "Hospital"),
        ("airport", "Airport"),
    )

    node_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    node_type = models.CharField(max_length=50, choices=NODE_TYPES)
    label = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("node_type", "label")

    def __str__(self):
        return f"{self.node_type}:{self.label}"


class MobilityEdge(models.Model):
    EDGE_TYPES = (
        ("assigned_to", "Assigned To"),
        ("located_at", "Located At"),
        ("travels_to", "Travels To"),
        ("connected_to", "Connected To"),
        ("operates_in", "Operates In"),
    )

    source = models.ForeignKey(
        MobilityNode,
        on_delete=models.CASCADE,
        related_name="outgoing_edges",
    )
    destination = models.ForeignKey(
        MobilityNode,
        on_delete=models.CASCADE,
        related_name="incoming_edges",
    )
    edge_type = models.CharField(max_length=50, choices=EDGE_TYPES)
    metadata = models.JSONField(default=dict)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("edge_type", "source_id", "destination_id")

    def __str__(self):
        return f"{self.source_id}->{self.destination_id}:{self.edge_type}"
