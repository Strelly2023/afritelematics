"""ritech/replay/generate.py

Phase‑2A transcript generator entrypoint
(Authority‑scoped replay artifacts)

This module is execution‑binding.
It MUST preserve Phase‑1 replay invariants while
introducing authority‑scoped artifact identity.
"""

from pathlib import Path
import sys
import yaml

from afritech.replay.transcript import (
    ReplayTranscriptGenerator,
    ConstitutionalRequest,
)


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

    # --------------------------------------------------------
    # Resolve request path
    # --------------------------------------------------------

    if len(sys.argv) == 1:
        request_path = DEFAULT_REQUEST_PATH
    elif len(sys.argv) == 2:
        request_path = Path(sys.argv[1])
    else:
        raise SystemExit(
            "Usage: python3 -m afritech.replay.generate [<request_path>]"
        )

    if not request_path.exists():
        raise FileNotFoundError(
            f"Request file not found: {request_path}"
        )

    # --------------------------------------------------------
    # Load request
    # --------------------------------------------------------

    with request_path.open("r", encoding="utf-8") as f:
        request_data = yaml.safe_load(f)

    if not isinstance(request_data, dict):
        raise ValueError("Invalid request payload format")

    request = ConstitutionalRequest(payload=request_data)

    # --------------------------------------------------------
    # Extract authority identity (Phase‑2A invariant)
    # --------------------------------------------------------

    try:
        authority_profile = (
            request.payload["constitutional_request"]["authority_profile"]
        )
    except KeyError as exc:
        raise KeyError(
            "Request missing constitutional_request.authority_profile"
        ) from exc

    authority_slug = authority_profile.lower()

    # --------------------------------------------------------
    # Authority‑scoped output path
    # --------------------------------------------------------

    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        TRANSCRIPT_DIR / f"{authority_slug}_v1.yaml"
    )

    # --------------------------------------------------------
    # Generate transcript
    # --------------------------------------------------------

    generator = ReplayTranscriptGenerator()
    generator.generate(
        request=request,
        output_path=str(output_path),
    )

    # --------------------------------------------------------
    # Stdout (evidence-safe)
    # --------------------------------------------------------

    print(f"Transcript written to {output_path}")


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    main()
