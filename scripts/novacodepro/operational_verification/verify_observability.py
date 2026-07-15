#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from afritech.novacodepro.operational_verification.observability import ObservabilityProviderConfig, verify_observability


def main() -> int:
    result = verify_observability(ObservabilityProviderConfig("opentelemetry", True), {"traces"}, False)
    print(result)
    return 1 if result.verified else 0


if __name__ == "__main__":
    raise SystemExit(main())
