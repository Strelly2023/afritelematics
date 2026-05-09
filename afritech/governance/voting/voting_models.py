from datetime import datetime


class VoteDecision:
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class Vote:

    def __init__(self, voter_id, decision, weight=1):
        self.voter_id = voter_id
        self.decision = decision
        self.weight = weight
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "voter_id": self.voter_id,
            "decision": self.decision,
            "weight": self.weight,
            "timestamp": self.timestamp
        }


class VotingSession:

    def __init__(self, adr_id, quorum_ratio=0.66):
        self.adr_id = adr_id
        self.votes = []
        self.quorum_ratio = quorum_ratio
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.closed = False

    def add_vote(self, vote: Vote):
        if self.closed:
            raise Exception("Voting session closed")

        # Prevent duplicate votes
        for v in self.votes:
            if v.voter_id == vote.voter_id:
                raise Exception("Voter already voted")

        self.votes.append(vote)

    def compute_result(self):

        total_weight = sum(v.weight for v in self.votes)
        approve_weight = sum(
            v.weight for v in self.votes if v.decision == VoteDecision.APPROVE
        )

        reject_weight = total_weight - approve_weight

        if total_weight == 0:
            return "NO_VOTES"

        approval_ratio = approve_weight / total_weight

        if approval_ratio >= self.quorum_ratio:
            return "APPROVED"
        elif reject_weight / total_weight >= self.quorum_ratio:
            return "REJECTED"
        else:
            return "PENDING"

    def to_dict(self):
        return {
            "adr_id": self.adr_id,
            "votes": [v.to_dict() for v in self.votes],
            "quorum_ratio": self.quorum_ratio,
            "result": self.compute_result(),
            "closed": self.closed,
            "created_at": self.created_at
        }