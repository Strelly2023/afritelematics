from afritech.constitution.verify_semantic_coverage import (
    verify_projection_consistency,
)

import pytest


def test_semantic_projection_consistency():

    canonical = {
        "I1",
        "I2",
        "I3",
    }

    semantic = {
        "I1",
        "I2",
    }

    compiled = {
        "I1",
    }

    index = {
        "I1",
    }

    verify_projection_consistency(
        canonical,
        semantic,
        compiled,
        index,
    )


def test_semantic_projection_unknown_invariant():

    canonical = {
        "I1",
        "I2",
    }

    semantic = {
        "I1",
        "I999",
    }

    compiled = {
        "I1",
    }

    index = {
        "I1",
    }

    with pytest.raises(SystemExit):

        verify_projection_consistency(
            canonical,
            semantic,
            compiled,
            index,
        )