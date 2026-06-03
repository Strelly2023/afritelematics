import json
from pathlib import Path
from afritech.governance.adr.adr_models import ADR


class ADRRepository:

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.store = self.base_path / "governance/adr/workflow"

        self.store.mkdir(parents=True, exist_ok=True)

    def save(self, adr: ADR):

        file_path = self.store / f"{adr.id}.json"

        with open(file_path, "w") as f:
            json.dump(adr.to_dict(), f, indent=2)

        return str(file_path)

    def load(self, adr_id: str):

        file_path = self.store / f"{adr_id}.json"

        if not file_path.exists():
            raise Exception("ADR not found")

        with open(file_path, "r") as f:
            data = json.load(f)

        adr = ADR(
            adr_id=data["id"],
            drift_report=data["drift_report"],
            context=data["context"]
        )

        adr.status = data["status"]
        adr.history = data["history"]

        return adr

    def list_all(self):
        return [f.name for f in self.store.glob("*.json")]
