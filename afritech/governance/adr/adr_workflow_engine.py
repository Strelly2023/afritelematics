import hashlib
from datetime import datetime

from afritech.governance.adr.adr_models import ADR, ADRStatus
from afritech.governance.adr.adr_repository import ADRRepository

# ✅ Policy engine

from afritech.governance.policy.policy_rules_engine import PolicyRulesEngine
from afritech.governance.policy.policy_models import PolicyDecision


class ADRWorkflowError(Exception):
    """Raised when ADR workflow operation fails"""
    pass


# -----------------------------------------------------------------
# ADR WORKFLOW ENGINE
# -----------------------------------------------------------------

class ADRWorkflowEngine:

    def __init__(self, base_path: str):

        self.repo = ADRRepository(base_path)

        # ✅ Policy engine (automatic governance decisions)
        self.policy_engine = PolicyRulesEngine()

    # -----------------------------------------------------------------
    # CREATE ADR FROM DRIFT
    # -----------------------------------------------------------------

    def create_from_drift(self, drift_report, context):

        adr_id = self._generate_id()

        adr = ADR(
            adr_id=adr_id,
            drift_report=drift_report.to_dict(),
            context=context
        )

        # -------------------------------------------------------------
        # ✅ APPLY POLICY RULES (AUTONOMOUS GOVERNANCE)
        # -------------------------------------------------------------
        decision_meta = self.policy_engine.evaluate(adr.to_dict())
        decision = decision_meta["decision"]
        rule = decision_meta["rule"]

        if decision == PolicyDecision.APPROVE:
            adr.transition(
                ADRStatus.APPROVED,
                actor="policy_engine",
                note=f"auto-approved:{rule}"
            )

        elif decision == PolicyDecision.REJECT:
            adr.transition(
                ADRStatus.REJECTED,
                actor="policy_engine",
                note=f"auto-rejected:{rule}"
            )

        else:
            adr.transition(
                ADRStatus.UNDER_REVIEW,
                actor="policy_engine",
                note=f"requires_vote:{rule}"
            )

        self.repo.save(adr)

        return adr

    # -----------------------------------------------------------------
    # SUBMIT FOR REVIEW (MANUAL PATH)
    # -----------------------------------------------------------------

    def submit_for_review(self, adr_id: str, actor: str):

        adr = self._load(adr_id)

        if adr.status != ADRStatus.PROPOSED:
            raise ADRWorkflowError("ADR must be in PROPOSED state")

        adr.transition(ADRStatus.UNDER_REVIEW, actor)
        self.repo.save(adr)

        return adr

    # -----------------------------------------------------------------
    # APPROVE
    # -----------------------------------------------------------------

    def approve(self, adr_id: str, actor: str):

        adr = self._load(adr_id)

        if adr.status not in [ADRStatus.UNDER_REVIEW, ADRStatus.PROPOSED]:
            raise ADRWorkflowError("ADR must be UNDER_REVIEW or PROPOSED")

        adr.transition(ADRStatus.APPROVED, actor)
        self.repo.save(adr)

        return adr

    # -----------------------------------------------------------------
    # REJECT
    # -----------------------------------------------------------------

    def reject(self, adr_id: str, actor: str):

        adr = self._load(adr_id)

        if adr.status not in [ADRStatus.UNDER_REVIEW, ADRStatus.PROPOSED]:
            raise ADRWorkflowError("ADR must be UNDER_REVIEW or PROPOSED")

        adr.transition(ADRStatus.REJECTED, actor)
        self.repo.save(adr)

        return adr

    # -----------------------------------------------------------------
    # APPLY (FINAL STEP)
    # -----------------------------------------------------------------

    def apply(self, adr_id: str, actor: str):

        adr = self._load(adr_id)

        if adr.status != ADRStatus.APPROVED:
            raise ADRWorkflowError("ADR must be APPROVED before applying")

        adr.transition(ADRStatus.APPLIED, actor)
        self.repo.save(adr)

        return adr

    # -----------------------------------------------------------------
    # GET ADR
    # -----------------------------------------------------------------

    def get(self, adr_id: str):
        return self._load(adr_id)

    # -----------------------------------------------------------------
    # LIST ADRs
    # -----------------------------------------------------------------

    def list_all(self):
        return self.repo.list_all()

    # -----------------------------------------------------------------
    # INTERNAL LOAD
    # -----------------------------------------------------------------

    def _load(self, adr_id: str):

        try:
            return self.repo.load(adr_id)
        except Exception as e:
            raise ADRWorkflowError(f"Failed to load ADR: {str(e)}")

    # -----------------------------------------------------------------
    # ID GENERATION (DETERMINISTIC)
    # -----------------------------------------------------------------

    def _generate_id(self):

        seed = datetime.utcnow().isoformat().encode()

        return "ADR-" + hashlib.sha256(seed).hexdigest()[:12]
