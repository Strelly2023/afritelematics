"""Guard for closed-world edge admission ordering."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


REQUIRED_EDGE_SEQUENCE = ("adapter", "normalization", "ingestion")


def validate_edge_pipeline(flow_trace: Mapping[str, Any]) -> None:
    """Ensure external input passed through adapter, normalization, ingestion."""

    stages = flow_trace.get("stages")
    if not isinstance(stages, Sequence) or isinstance(stages, (str, bytes)):
        raise ValueError("Edge pipeline trace must include ordered stages")

    if tuple(stages) != REQUIRED_EDGE_SEQUENCE:
        raise ValueError("Edge pipeline violated")

