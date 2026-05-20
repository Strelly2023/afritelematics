from runtime.activation.runtime_admission import (
    RuntimeAdmissionValidator,
    RuntimeAdmissionError,
)

from replay.binding.replay_binding_engine import (
    ReplayBindingEngine,
    ReplayTranscript,
    TruthPacket,
)

from evaluation.drift.drift_detection_engine import (
    DriftDetectionEngine,
    DriftDetectionError,
)

from evaluation.persistence.transcript_store import TranscriptStore

from governance.adr.adr_auto_trigger import (
    ADRAutoTrigger,
    ADRStore,
)

# ✅ Optional distributed consensus
from network.consensus.distributed_consensus import DistributedConsensus


# -----------------------------------------------------------------
# CONSTITUTIONAL RUNTIME
# -----------------------------------------------------------------

class ConstitutionalRuntime:

    def __init__(self, base_path: str, consensus_engine: DistributedConsensus = None):
        self.base_path = base_path

        # Core validator
        self.validator = RuntimeAdmissionValidator(base_path)

        # Engines (initialized at boot)
        self.replay_engine = None
        self.drift_engine = None

        # Optional distributed consensus
        self.consensus_engine = consensus_engine

        # Persistence
        self.transcript_store = TranscriptStore(base_path)

        # ADR governance
        self.adr_store = ADRStore(base_path)
        self.adr_trigger = ADRAutoTrigger(self.validator, self.adr_store)

        # Drift baseline
        self.baseline_transcript = None

    # -----------------------------------------------------------------
    # BOOT (ADMISSION GATE)
    # -----------------------------------------------------------------

    def boot(self):

        try:
            if not self.validator.validate():
                raise RuntimeAdmissionError("Runtime admission failed")

            # ✅ Initialize engines only after validation
            self.replay_engine = ReplayBindingEngine(self.validator)
            self.drift_engine = DriftDetectionEngine(self.validator)

            print("✅ Runtime admitted under constitutional law")

            return True

        except RuntimeAdmissionError as e:
            print(f"❌ HARD FAILURE: {str(e)}")
            raise SystemExit(1)

    # -----------------------------------------------------------------
    # EXECUTION ENTRY POINT
    # -----------------------------------------------------------------

    def execute(self, request: dict, execution_fn):

        if not self.replay_engine:
            raise RuntimeAdmissionError("Runtime not booted")

        # -------------------------------------------------------------
        # 1. EXECUTION (LOCAL OR DISTRIBUTED)
        # -------------------------------------------------------------
        if self.consensus_engine:

            consensus_result = self.consensus_engine.execute_with_consensus(request)
            replay_result = consensus_result["result"]
            consensus_meta = consensus_result["consensus"]

        else:
            response = execution_fn(request)

            replay_result = self.replay_engine.bind_and_verify(
                request,
                response
            )

            consensus_meta = None

        # -------------------------------------------------------------
        # 2. REBUILD FULL TRANSCRIPT (CRITICAL)
        # -------------------------------------------------------------
        transcript = self._rebuild_transcript(replay_result)

        # -------------------------------------------------------------
        # 3. PERSIST TRANSCRIPT (IMMUTABLE LEDGER)
        # -------------------------------------------------------------
        entry = self.transcript_store.store_transcript(transcript)

        # -------------------------------------------------------------
        # 4. DRIFT DETECTION
        # -------------------------------------------------------------
        try:

            if self.baseline_transcript is None:
                self.baseline_transcript = transcript
            else:
                self.drift_engine.check_drift(
                    self.baseline_transcript,
                    transcript
                )

        except DriftDetectionError as drift_error:

            drift_report = drift_error.report

            # ---------------------------------------------------------
            # 5. ADR AUTO-TRIGGER (GOVERNANCE)
            # ---------------------------------------------------------
            adr_result = self.adr_trigger.trigger_on_drift(
                drift_report
            )

            # ---------------------------------------------------------
            # HARD FAIL AFTER GOVERNANCE ESCALATION
            # ---------------------------------------------------------
            raise RuntimeAdmissionError({
                "error": "DRIFT_DETECTED",
                "adr": adr_result,
                "baseline": drift_report.baseline_hash,
                "current": drift_report.current_hash
            })

        # -------------------------------------------------------------
        # SUCCESS RESPONSE
        # -------------------------------------------------------------
        return {
            **replay_result,
            "consensus": consensus_meta,
            "persistence_entry_hash": entry["entry_hash"]
        }

    # -----------------------------------------------------------------
    # TRANSCRIPT RECONSTRUCTION (CRITICAL INTEGRITY)
    # -----------------------------------------------------------------

    def _rebuild_transcript(self, replay_result):

        truth_packet = TruthPacket(
            request=replay_result["truth_packet"]["request"],
            response=replay_result["truth_packet"]["response"],
            metadata=replay_result["truth_packet"]["metadata"]
        )

        return ReplayTranscript(
            truth_packet=truth_packet,
            runtime_certificate_hash=replay_result["runtime_certificate_hash"],
            attestation_hash=replay_result["attestation_hash"]
        )
