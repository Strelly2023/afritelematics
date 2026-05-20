import uuid
from datetime import datetime


class DomainEvent:
    def __init__(self, event_type, payload, metadata=None):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.payload = payload
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
