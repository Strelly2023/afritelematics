"""
State canonicalization utilities.

This module is dependency-neutral by design.
It must not import runtime, guards, or transitions.
"""

from __future__ import annotations


def canonicalize(value):
    """
    Pure canonicalization helper.
    No side effects.
    """
    # existing _canonicalize logic goes here
    return value