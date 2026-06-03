"""Edge ingestion admits normalized inputs into controlled queues."""

from afritech.edge.ingestion.queue_ingestor import ingest_event
from afritech.edge.ingestion.reality_ingestor import (
    admit_normalized_reality_events,
    ingest_normalized_reality_events,
)

__all__ = [
    "admit_normalized_reality_events",
    "ingest_event",
    "ingest_normalized_reality_events",
]
