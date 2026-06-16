"""Institutional mobility invariant surface bound by governance artifacts.

This module provides a stable target for governance bindings that separate the
institutional network implementation from its replay-safe invariant evaluation
surface.
"""

from __future__ import annotations

from afritech.mobility.institutional_networks import (
    INSTITUTION_INVARIANT_IDS,
    INVARIANT_AUTHORITY_BOUNDARY,
    InstitutionInvariantCheck,
    InstitutionInvariantReport,
    evaluate_institution_invariants,
    export_institution_invariant_report,
    validate_institution_invariants,
)


__all__ = [
    "INSTITUTION_INVARIANT_IDS",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "InstitutionInvariantCheck",
    "InstitutionInvariantReport",
    "evaluate_institution_invariants",
    "export_institution_invariant_report",
    "validate_institution_invariants",
]
