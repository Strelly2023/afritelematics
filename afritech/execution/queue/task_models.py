from datetime import datetime
import uuid


class TaskStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExecutionTask:

    def __init__(self, payload):
        self.id = str(uuid.uuid4())
        self.payload = payload

        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None

        self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at
        }
