"""Edge normalization converts adapted requests into replay-stable inputs."""

from afritech.edge.normalization.normalizer import normalize_input
from afritech.edge.normalization.reality_events import normalize_reality_events

__all__ = ["normalize_input", "normalize_reality_events"]
