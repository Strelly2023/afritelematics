"""
afritech/replay/run_verify.py

Constitutional replay verification entrypoint.

Phase‑2A:
- Supports authority‑scoped replay artifacts
- Enables cross‑authority rejection tests
"""

from afritech.replay.verify import ReplayVerifier
from afritech.replay.transcript import ConstitutionalRequest
from pathlib import Path
from typing import NoReturn
import yaml
import sys


# ============================================================
# DEFAULTS (PHASE‑1 COMPATIBLE)
# ============================================================

DEFAULT_REQUEST_PATH = Path(
    "afritech/inference/instances/research_agent_request_v1.yaml"
)

DEFAULT_TRANSCRIPT_PATH = Path(
    "afritech/replay/transcripts/constitutional_research_agent_v1.yaml"
)


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> NoReturn:
    """
    Verify a replay transcript against a constitutional request.

    Usage:
      python3 -m afritech.replay.run_verify
      python3 -m afritech.replay.run_verify <request_path> <transcript_path>

    Outputs are intentionally minimal and verbatim-friendly,
    to allow direct inclusion as admissible runtime artifacts.
    """

    # --------------------------------------------------------
    # Resolve CLI arguments
    # --------------------------------------------------------

    if len(sys.argv) == 1:
        request_path = DEFAULT_REQUEST_PATH
        transcript_path = DEFAULT_TRANSCRIPT_PATH

    elif len(sys.argv) == 3:
        request_path = Path(sys.argv[1])
        transcript_path = Path(sys.argv[2])

    else:
        raise SystemExit(
            "Usage: python3 -m afritech.replay.run_verify "
            "[<request_path> <transcript_path>]"
        )

    # --------------------------------------------------------
    # Resolve filesystem inputs
    # --------------------------------------------------------

    if not request_path.exists():
        raise FileNotFoundError(
            f"Request file not found: {request_path}"
        )

    if not transcript_path.exists():
        raise FileNotFoundError(
            f"Transcript file not found: {transcript_path}"
        )

    # --------------------------------------------------------
    # Load request
    # --------------------------------------------------------

    with request_path.open("r", encoding="utf-8") as f:
        request_payload = yaml.safe_load(f)

    request = ConstitutionalRequest(
        payload=request_payload
    )

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    verifier = ReplayVerifier()
    verdict = verifier.verify(
        transcript_path=str(transcript_path),
        request=request,
    )

    # --------------------------------------------------------
    # Output (verbatim, audit-safe)
    # --------------------------------------------------------

    print("VERDICT:", verdict.status)
    print("REPLAY_HASH:", verdict.replay_hash)
    print("FAILURE_MODE:", verdict.failure_mode)
    print("DIVERGENCE_LOCATION:", verdict.divergence_location)
    print("VIOLATED_INVARIANT:", verdict.violated_invariant)


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    main()