"""Compatibility wrapper for the canonical AfriTech feature catalog."""

from __future__ import annotations

from afritech.features import (
    FEATURES,
    SYSTEM_STATUS,
    evidence_complete,
    feature_by_id,
    feature_ids,
    feature_matrix,
    feature_names,
    incomplete_features,
    status_summary,
)


if __name__ == "__main__":
    print(status_summary())
    for feature in FEATURES:
        print(f"- {feature.name}: {feature.use}")
