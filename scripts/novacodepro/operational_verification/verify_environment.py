#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from afritech.novacodepro.operational_verification.status import invariant_status


def main() -> int:
    print(invariant_status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
