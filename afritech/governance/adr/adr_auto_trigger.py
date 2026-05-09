import hashlib
import json
from pathlib import Path
from datetime import datetime


class ADRAutoTriggerError(Exception):
    """Raised when ADR trigger fails"""
    pass


# -----------------------------------------------------------------
# ADR PROPOSAL (LEGACY / COMPAT MODE ONLY)
# NOTE: Primary system now uses ADRWorkflowEngine
# -----------------------------------------------------------------

class ADRProposal:

    def __init__(self, drift_report, context):
        self.id = self._generate_id()
        self.type = "DRIFT_TRIGGERED_ADR"

        self.drift_report = drift_report.to_dict()
        self.context = context

        self.status = "PROPOSED"
        self.created_at = datetime.utcnow().isoformat() + "Z"

    # -----------------------------------------------------------------
    # INTERNAL UTIL
    # -----------------------------------------------------------------

    def _generate_id(self):
        seed = datetime.utcnow().isoformat().encode()
        return "ADR-" + hashlib.sha256(seed).hexdigest()[:10]

    # -----------------------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------------------

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "drift_report": self.drift_report,
            "context": self.context,
            "created_at": self.created_at
        }

    def canonical(self):
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":")
        )

    def hash(self):
        return hashlib.sha256(self.canonical().encode()).hexdigest()


# -----------------------------------------------------------------
# ADR STORE (LEGACY IMMUTABLE RECORD)
# NOTE: Workflow engine should be primary storage
# -----------------------------------------------------------------

class ADRStore:

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.store_path = self.base_path / "governance/adr/store"

        self.store_path.mkdir(parents=True, exist_ok=True)

    def write_adr(self, adr: ADRProposal):

        data = adr.to_dict()
        adr_hash = adr.hash()

        file_name = f"{adr.id}_{adr_hash}.json"
        file_path = self.store_path / file_name

        # ✅ Canonical write (not pretty JSON)
        with open(file_path, "w") as f:
            f.write(
                json.dumps(
                    data,
                    sort_keys=True,
                    separators=(",", ":")
                )
            )

        return {
            "adr_id": adr.id,
            "adr_hash": adr_hash,
            "path": str(file_path)
        }

    def list_adrs(self):
        return sorted([f.name for f in self.store_path.glob("*.json")])


# -----------------------------------------------------------------
# ADR AUTO-TRIGGER ENGINE (PRIMARY GOVERNANCE ENTRY POINT)
# -----------------------------------------------------------------

class ADRAutoTrigger:

    def __init__(self, validator, base_path: str, adr_store: ADRStore = None):
        """
        validator: RuntimeAdmissionValidator
        base_path: required for ADRWorkflowEngine
        adr_store: optional (legacy support only)
        """

        self.validator = validator
        self.base_path = base_path

        # Optional legacy store
        self.adr_store = adr_store

        # ✅ PRIMARY: Workflow engine (governance layer)
        from governance.adr.adr_workflow_engine import ADRWorkflowEngine
        self.workflow = ADRWorkflowEngine(base_path)

    # -----------------------------------------------------------------
    # CONTEXT BUILDER (DETERMINISTIC SYSTEM SNAPSHOT)
    # -----------------------------------------------------------------

    def build_context(self):

        return {
            "epoch": self.validator.registry["epoch"]["current"],
            "registry_hash": self.validator.compute_registry_hash(),
            "kernel_hash": self.validator.compute_kernel_root_hash(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    # -----------------------------------------------------------------
    # MAIN TRIGGER (DRIFT → ADR WORKFLOW)
    # -----------------------------------------------------------------

    def trigger_on_drift(self, drift_report):

        try:
            context = self.build_context()

            # ---------------------------------------------------------
            # PRIMARY PATH → WORKFLOW ENGINE
            # ---------------------------------------------------------
            adr = self.workflow.create_from_drift(
                drift_report,
                context
            )

            result = {
                "trigger": "ADR_CREATED",
                "adr_id": adr.id,
                "status": adr.status,
                "path": "workflow_engine",
            }

            # ---------------------------------------------------------
            # OPTIONAL LEGACY STORE (PARALLEL WRITE)
            # ---------------------------------------------------------
            if self.adr_store:

                legacy_adr = ADRProposal(drift_report, context)
                stored = self.adr_store.write_adr(legacy_adr)

                result["legacy_record"] = stored

            return result

        except Exception as e:
            raise ADRAutoTriggerError(
                f"Failed to trigger ADR: {str(e)}"
            )