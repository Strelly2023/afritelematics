#!/usr/bin/env python3
"""Generate the AfriTech full architecture graph from repo facts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from afritech.architecture.full_architecture_graph import write_architecture_graph


def main() -> int:
    output = write_architecture_graph()
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
