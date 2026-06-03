"""
AfriTech Async + Locality Tests

PURPOSE:
--------
Validate locality layer:

- region resolution
- partition routing
- node selection
- queue naming
- deterministic placement

CRITICAL GUARANTEE:
------------------
Locality MUST NOT affect event semantics
"""

import pytest

from afritech.runtime.locality.locality_manager import (
    resolve_execution_location,
    resolve_queue_name,
)

#afritech/tests/runtime/test_async_locality.py

# ============================================================
# ✅ TEST CONTEXT
# ============================================================

class DummyContext:
    def __init__(self):
        self.policy = {
            "transport_mode": "test",
            "default_region": "global",
            "partition_count": 10,
        }


@pytest.fixture
def context():
    return DummyContext()


# ============================================================
# ✅ LOCATION RESOLUTION TEST
# ============================================================

def test_execution_location(context):
    event = {
        "event_id": "1",
        "payload": {"value": 1},
        "timestamp": "2026-01-01",
        "region": "au",
    }

    location = resolve_execution_location(event, context)

    assert "region" in location
    assert "partition" in location
    assert "node" in location


# ============================================================
# ✅ DEFAULT REGION TEST
# ============================================================

def test_default_region(context):
    event = {
        "event_id": "2",
        "payload": {"value": 2},
        "timestamp": "2026-01-01",
    }

    location = resolve_execution_location(event, context)

    assert location["region"] == "global"


# ============================================================
# ✅ PARTITION DETERMINISM
# ============================================================

def test_partition_determinism(context):
    event = {
        "event_id": "abc",
        "payload": {},
        "timestamp": "2026-01-01",
    }

    loc1 = resolve_execution_location(event, context)
    loc2 = resolve_execution_location(event, context)

    assert loc1["partition"] == loc2["partition"]


# ============================================================
# ✅ NODE DETERMINISM
# ============================================================

def test_node_determinism(context):
    event = {
        "event_id": "xyz",
        "payload": {},
        "timestamp": "2026-01-01",
    }

    loc1 = resolve_execution_location(event, context)
    loc2 = resolve_execution_location(event, context)

    assert loc1["node"] == loc2["node"]


# ============================================================
# ✅ QUEUE NAME TEST
# ============================================================

def test_queue_name_creation(context):
    event = {
        "event_id": "10",
        "payload": {},
        "timestamp": "2026-01-01",
    }

    queue_name = resolve_queue_name(event, context)

    assert queue_name.startswith("events.")


# ============================================================
# ✅ REGION NORMALIZATION
# ============================================================

def test_region_normalization(context):
    event = {
        "event_id": "11",
        "payload": {},
        "timestamp": "2026-01-01",
        "region": "AU ",
    }

    loc = resolve_execution_location(event, context)

    assert loc["region"] == "au"


# ============================================================
# ✅ LOCALITY DOES NOT MUTATE EVENT
# ============================================================

def test_locality_no_mutation(context):
    event = {
        "event_id": "immut",
        "payload": {"x": 1},
        "timestamp": "2026-01-01",
    }

    copy = dict(event)

    _ = resolve_execution_location(event, context)

    assert event == copy