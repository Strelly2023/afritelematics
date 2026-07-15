#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from afritech.novacodepro.operational_verification.prr import generate_prr_package, validate_prr_package


def main() -> int:
    print(validate_prr_package(generate_prr_package("release-pending", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
