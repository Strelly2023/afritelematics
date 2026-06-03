"""
afritech.distributed.api.replay

🔒 OPERATIVE SURFACE

Approved public interface for distributed replay verification.

All consumers MUST import from this module instead of internal replay modules.

Ensures:
- constitutional import topology compliance
- deterministic replay validation
- strict execution verification guarantees
"""

# ============================================================
# REPLAY VERIFICATION (CORE)
# ============================================================

from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
    DistributedReplayVerificationError,
    DistributedReplayVerificationReport,
    DistributedWorkerResult,
    build_worker_result,
    verify_distributed_replay,
    require_distributed_replay_verified,
)

# ✅ COMPATIBILITY ALIAS (tests + legacy systems)
verify_replay_transcript = verify_distributed_replay


# ============================================================
# REPLAY LEDGER (STATE TRACKING)
# ============================================================

from afritech.distributed.replay.distributed_ledger import (
    DistributedReplayLedger,
    DistributedLedgerError,
    DistributedLedgerSnapshot,
    DistributedLedgerEntry,
)


# ============================================================
# EXECUTION TRANSCRIPTS (AUDIT + TRACE LAYER)
# ============================================================

from afritech.distributed.replay.distributed_execution_transcript import (
    DistributedExecutionTranscript,
    DistributedExecutionTranscriptEntry,
    DistributedExecutionTranscriptVerification,
    verify_distributed_execution_transcript,
    require_valid_distributed_execution_transcript,
    transcript_from_mappings,
)


# ============================================================
# OPTIONAL UTILITIES (SAFE EXPOSURE)
# ============================================================

from afritech.distributed.replay.distributed_replay_verifier import (
    build_distributed_execution_hash,
    build_replay_reconstruction_hash,
)


# ============================================================
# VERSION + METADATA (OPTIONAL BUT USEFUL)
# ============================================================

API_VERSION = "1.0.0"
API_SURFACE = "distributed.replay"


# ============================================================
# PUBLIC EXPORTS ✅ STRICT
# ============================================================

__all__ = [

    # ---------------------------------------------------------
    # CORE REPLAY VERIFICATION
    # ---------------------------------------------------------
    "DistributedReplayTranscript",
    "DistributedReplayVerificationError",
    "DistributedReplayVerificationReport",
    "DistributedWorkerResult",
    "build_worker_result",
    "verify_distributed_replay",
    "verify_replay_transcript",
    "require_distributed_replay_verified",

    # ---------------------------------------------------------
    # LEDGER
    # ---------------------------------------------------------
    "DistributedReplayLedger",
    "DistributedLedgerError",
    "DistributedLedgerSnapshot",
    "DistributedLedgerEntry",

    # ---------------------------------------------------------
    # EXECUTION TRANSCRIPT (AUDIT LAYER)
    # ---------------------------------------------------------
    "DistributedExecutionTranscript",
    "DistributedExecutionTranscriptEntry",
    "DistributedExecutionTranscriptVerification",
    "verify_distributed_execution_transcript",
    "require_valid_distributed_execution_transcript",
    "transcript_from_mappings",

    # ---------------------------------------------------------
    # HASH / REPLAY UTILITIES
    # ---------------------------------------------------------
    "build_distributed_execution_hash",
    "build_replay_reconstruction_hash",

    # ---------------------------------------------------------
    # METADATA
    # ---------------------------------------------------------
    "API_VERSION",
    "API_SURFACE",
]