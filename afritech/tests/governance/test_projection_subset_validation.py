from afritech.ci.invariant_validator import (
    validate_runtime_projection,
)

import pytest


def test_projection_subset_valid():

    registry = {
        "I1",
        "I2",
        "I3",
    }

    projection = {
        "I1",
        "I2",
    }

    validate_runtime_projection(
        registry,
        projection,
        "runtime",
    )


def test_projection_subset_invalid():

    registry = {
        "I1",
        "I2",
    }

    projection = {
        "I1",
        "I99_UNKNOWN",
    }

    with pytest.raises(Exception):

        validate_runtime_projection(
            registry,
            projection,
            "runtime",
        )