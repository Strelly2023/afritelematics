#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from afritech.novacodepro.operational_verification.visual_regression import verify_visual_regression


def main() -> int:
    result = verify_visual_regression(None, tool_ran=False)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
