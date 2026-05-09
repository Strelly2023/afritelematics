import hashlib
import json
from datetime import datetime


class DriftDetectionError(Exception):
    """
    Raised when drift detection fails.

    IMPORTANT:
    Carries structured DriftReport (not just string)
    for ADR auto-trigger and audit usage.
    """

    def __init__(self, report):
        self.report = report
        super().__init__(self._format_message())

    def _format_message(self):
        return (
            f"Drift detected: baseline={self.report.baseline_hash} "
            f"current={self.report.current_hash}"
        )


# -----------------------------------------------------------------
# DRIFT REPORT (AUDIT ARTIFACT)
# -----------------------------------------------------------------

class DriftReport:

    def __init__(self, baseline_hash, current_hash, drift_detected, details):
        self.baseline_hash = baseline_hash
        self.current_hash = current_hash
        self.drift_detected = drift_detected
        self.details = details

        # ✅ UTC timestamp (NON-COMPARABLE FIELD)
        self.generated_at = datetime.utcnow().isoformat() + "Z"

    # -----------------------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------------------

    def to_dict(self):
        return {
            "baseline_hash": self.baseline_hash,
            "current_hash": self.current_hash,
            "drift_detected": self.drift_detected,
            "details": self.details,
            "generated_at": self.generated_at
        }

    def canonical(self):
        """
        Deterministic serialization for audit hashing.
        Includes timestamp because this is an audit artifact.
        """
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":")
        )

    def hash(self):
        return hashlib.sha256(self.canonical().encode()).hexdigest()


# -----------------------------------------------------------------
# DRIFT DETECTOR (CORE LOGIC)
# -----------------------------------------------------------------

class DriftDetector:

    def __init__(self, threshold=0.0):
        """
        threshold:
            0.0 → strict deterministic equality (REQUIRED)
            >0  → reserved for future similarity scoring
        """
        self.threshold = threshold

    # -----------------------------------------------------------------
    # HASH COMPARISON
    # -----------------------------------------------------------------

    def compare_hashes(self, baseline_hash, current_hash):
        return baseline_hash == current_hash

    # -----------------------------------------------------------------
    # DRIFT DETECTION
    # -----------------------------------------------------------------

    def detect_drift(self, baseline_transcript, current_transcript):
        """
        Drift is evaluated using transcript.hash()

        IMPORTANT:
        transcript.hash() MUST exclude:
            - generated_at timestamps
            - any non-deterministic fields
        """

        baseline_hash = baseline_transcript.hash()
        current_hash = current_transcript.hash()

        drift_detected = not self.compare_hashes(
            baseline_hash,
            current_hash
        )

        details = {
            "comparison": "deterministic_transcript_hash",
            "baseline_hash": baseline_hash,
            "current_hash": current_hash
        }

        return DriftReport(
            baseline_hash=baseline_hash,
            current_hash=current_hash,
            drift_detected=drift_detected,
            details=details
        )


# -----------------------------------------------------------------
# DRIFT DETECTION ENGINE (ENFORCEMENT LAYER)
# -----------------------------------------------------------------

class DriftDetectionEngine:

    def __init__(self, validator):
        self.validator = validator
        self.detector = DriftDetector()

        # ✅ Internal baseline tracking
        self._baseline_hash = None

    # -----------------------------------------------------------------
    # BASELINE MANAGEMENT
    # -----------------------------------------------------------------

    def generate_baseline(self, transcript):
        """
        Establish baseline from a transcript.
        """
        baseline_hash = transcript.hash()
        self._baseline_hash = baseline_hash
        return baseline_hash

    def has_baseline(self):
        return self._baseline_hash is not None

    def get_baseline_hash(self):
        return self._baseline_hash or "UNSET"

    # -----------------------------------------------------------------
    # DRIFT CHECK (FULL TRANSCRIPT)
    # -----------------------------------------------------------------

    def check_drift(self, baseline_transcript, current_transcript):

        report = self.detector.detect_drift(
            baseline_transcript,
            current_transcript
        )

        if report.drift_detected:
            self.handle_drift(report)

        return report

    # -----------------------------------------------------------------
    # DRIFT CHECK (HASH-ONLY OPTIMIZED PATH)
    # -----------------------------------------------------------------

    def check_drift_by_hash(self, baseline_hash, current_transcript):

        current_hash = current_transcript.hash()

        drift_detected = baseline_hash != current_hash

        report = DriftReport(
            baseline_hash=baseline_hash,
            current_hash=current_hash,
            drift_detected=drift_detected,
            details={
                "comparison": "hash_only",
                "baseline_hash": baseline_hash,
                "current_hash": current_hash
            }
        )

        if drift_detected:
            self.handle_drift(report)

        return report

    # -----------------------------------------------------------------
    # ENFORCEMENT HOOK (CRITICAL)
    # -----------------------------------------------------------------

    def handle_drift(self, report: DriftReport):
        """
        Constitutional enforcement:

        - NO silent drift
        - MUST escalate to ADR layer
        - MUST preserve full DriftReport
        """

        raise DriftDetectionError(report)
