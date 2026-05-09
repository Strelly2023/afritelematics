import json
from pathlib import Path
from governance.voting.voting_models import Vote, VotingSession


class VotingRepository:

    def __init__(self, base_path: str):
        self.store = Path(base_path) / "governance/voting"
        self.store.mkdir(parents=True, exist_ok=True)

    def save(self, session: VotingSession):
        file_path = self.store / f"{session.adr_id}.json"

        with open(file_path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

    def load(self, adr_id: str):

        file_path = self.store / f"{adr_id}.json"

        if not file_path.exists():
            raise Exception("Voting session not found")

        with open(file_path, "r") as f:
            data = json.load(f)

        session = VotingSession(
            adr_id=data["adr_id"],
            quorum_ratio=data["quorum_ratio"]
        )

        session.votes = [
            Vote(**v) for v in data["votes"]
        ]

        session.closed = data["closed"]

        return session
