from afritech.ci.invariant_validator import (
    invariant_sort_key,
    validate_deterministic_ordering,
)

import pytest


def test_invariant_sort_key_numeric_order():

    ids = [
        "I10_CONSENSUS",
        "I2_SURFACE",
        "I1_AUTHORITY",
        "I15_FINAL",
    ]

    ordered = sorted(
        ids,
        key=invariant_sort_key,
    )

    assert ordered == [
        "I1_AUTHORITY",
        "I2_SURFACE",
        "I10_CONSENSUS",
        "I15_FINAL",
    ]


def test_deterministic_ordering_accepts_valid():

    ids = [
        "I1_AUTHORITY",
        "I2_SURFACE",
        "I3_MUTATION",
    ]

    validate_deterministic_ordering(ids)


def test_deterministic_ordering_rejects_invalid():

    ids = [
        "I2_SURFACE",
        "I1_AUTHORITY",
    ]

    with pytest.raises(Exception):

        validate_deterministic_ordering(ids)