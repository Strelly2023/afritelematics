"""
afritech/replay/generate.py

Phase‑2A transcript generator entrypoint
(Authority‑scoped replay artifacts)

This module is execution‑binding.
It MUST preserve Phase‑1 replay invariants while
introducing authority‑scoped artifact identity.
"""

from afritech.replay.transcript import (
    ReplayTranscriptGenerator,
    ConstitutionalRequest,
)
import yaml
from pathlib import Path
import sys


# ============================================================
# CONFIG
# ============================================================

DEFAULT_REQUEST_PATH = Path(
    "afritech/inference/instances/research_agent_request_v1.yaml"
)

TRANSCRIPT_DIR = Path(
    "afritech/replay/transcripts"
)


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> None:
    """
    Generate a replay transcript under the authority
    declared in the request artifact.

    Authority identity is part of transcript identity.
    """

    # --------------------------------------------
    # Resolve request path
    # --------------------------------------------

    if len(sys.argv) > 1:
        request_path = Path(sys.argv[1])
    else:
        request_path = DEFAULT_REQUEST_PATH

    if not request_path.exists():
        raise FileNotFoundError(
            f"Request file not found: {request_path}"
        )

    # --------------------------------------------
    # Load request
    # --------------------------------------------

    with request_path.open("r", encoding="utf-8") as f:
        request_data = yaml.safe_load(f)

    request = ConstitutionalRequest(payload=request_data)

    authority = (
        request.payload["constitutional_request"]
        ["authority_profile"]
        .lower()
    )

    # --------------------------------------------
    # Authority‑scoped output path
    # --------------------------------------------

    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        TRANSCRIPT_DIR
        / f"{authority}_v1.yaml"
    )

    # --------------------------------------------
    # Generate transcript
    # --------------------------------------------

    generator = ReplayTranscriptGenerator()
    generator.generate(
        request=request,
        output_path=str(output_path),
    )

    print(f"Transcript written to {output_path}")


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    main()