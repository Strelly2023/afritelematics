#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from afritech.novacodepro.operational_verification.accessibility import AccessibilityRunConfig, verify_accessibility


def main() -> int:
    result = verify_accessibility(AccessibilityRunConfig(("/",)), tools_ran=False)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
