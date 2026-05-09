from datetime import datetime


class ADRStatus:
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"


class ADR:

    def __init__(self, adr_id, drift_report, context):
        self.id = adr_id
        self.status = ADRStatus.PROPOSED

        self.drift_report = drift_report
        self.context = context

        self.history = []
        self.created_at = datetime.utcnow().isoformat() + "Z"

    def transition(self, new_status, actor, note=""):

        self.history.append({
            "from": self.status,
            "to": new_status,
            "actor": actor,
            "note": note,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        self.status = new_status

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "drift_report": self.drift_report,
            "context": self.context,
            "history": self.history,
            "created_at": self.created_at
        }