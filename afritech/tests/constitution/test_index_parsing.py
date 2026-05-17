from pathlib import Path

from afritech.ci.invariant_validator import (
    parse_index_ids,
)


def test_index_parsing_filters_non_invariants(
    tmp_path,
):

    content = '''
I1_AUTHORITY = "I1_AUTHORITY"
I2_SURFACE = "I2_SURFACE"

INVARIANT_COUNT = 2
SCHEMA_VERSION = "v1"

NOT_AN_INVARIANT = "x"
'''

    path = (
        tmp_path
        / "invariants_index.py"
    )

    path.write_text(content)

    ids = parse_index_ids(path)

    assert ids == [
        "I1_AUTHORITY",
        "I2_SURFACE",
    ]


def test_index_parsing_empty(
    tmp_path,
):

    path = (
        tmp_path
        / "empty.py"
    )

    path.write_text("")

    ids = parse_index_ids(path)

    assert ids == []