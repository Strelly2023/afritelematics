#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from afritech.novacodepro.operational_verification.digital_twin import TelemetryProfile, verify_telemetry_profile


def main() -> int:
    print(verify_telemetry_profile(TelemetryProfile(0, False, False, False, False, False, False, True)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
