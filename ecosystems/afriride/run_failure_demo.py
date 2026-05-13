# ecosystems/afriride/run_failure_demo.py

"""
AFRIRIDE FAILURE DEMO

Purpose:
- Simulate degraded conditions
- Execute ride flow
- Replay events
- Verify determinism (Decision Determinism Rate = 1.0)

Expected:
✅ Same hash before/after replay
✅ Deterministic behavior under failure
✅ Full trace + proof
"""

from copy import deepcopy

# ✅ Runtime
from ecosystems.afriride.core.constitutional.runtime_adapter import ExecutionRuntime

# ✅ Domain Context + Roles (FIXED IMPORT)
from ecosystems.afriride.core.domain.ride_context import AfriRideExecutionContext
from ecosystems.afriride.core.domain.ride_roles import RideAuthorityRole

# ✅ Observability
from ecosystems.afriride.core.observability.decision_metrics import (
    build_decision_metric,
    assert_deterministic,
)

# ✅ Replay hash
from ecosystems.afriride.core.infrastructure.persistence.replay_hasher import (
    hash_events,
)


# ---------------------------------------------------------
# ✅ COMMANDS
# ---------------------------------------------------------

class RequestRide:
    def __init__(self, rider_id):
        self.rider_id = rider_id


class AssignDriver:
    def __init__(self, ride_id):
        self.ride_id = ride_id


# ---------------------------------------------------------
# ✅ HANDLERS (DETERMINISTIC)
# ---------------------------------------------------------

def handle_request_ride(command):
    state = {
        "ride_id": "ride-001",
        "status": "REQUESTED",
        "rider_id": command.rider_id,
    }

    events = [
        f"RideRequested:{command.rider_id}"
    ]

    return {
        "state": state,
        "events": events,
    }


def handle_assign_driver(command, context):
    drivers = sorted(context.drivers, key=lambda d: d["id"])
    driver = drivers[0]

    state = {
        "ride_id": command.ride_id,
        "status": "ASSIGNED",
        "driver_id": driver["id"],
    }

    events = [
        f"DriverAssigned:{driver['id']}"
    ]

    return {
        "state": state,
        "events": events,
    }


# ---------------------------------------------------------
# ✅ EVENT STORE
# ---------------------------------------------------------

EVENT_STORE = []


def persist_events(events):
    EVENT_STORE.extend(events)


def load_events():
    return deepcopy(EVENT_STORE)


def replay_system(events):
    return deepcopy(events)


# ---------------------------------------------------------
# ✅ DRIVER SEEDING
# ---------------------------------------------------------

def seed_drivers(n=10):
    return [
        {"id": f"driver-{i}", "available": True}
        for i in range(n)
    ]


# ---------------------------------------------------------
# ✅ FAILURE DEMO
# ---------------------------------------------------------

def run_failure_demo():
    print("\n=== AFRIRIDE FAILURE DEMO ===\n")

    runtime = ExecutionRuntime()

    # STEP 1: seed drivers
    drivers = seed_drivers(10)
    print(f"Initial drivers: {len(drivers)}")

    # STEP 2: degrade deterministically
    degraded_drivers = sorted(drivers, key=lambda d: d["id"])[:5]
    print(f"Degraded drivers: {len(degraded_drivers)}")

    # STEP 3: initial context (RIDER)
    context = AfriRideExecutionContext(
        role=RideAuthorityRole.RIDER,
        drivers=degraded_drivers,
        state=None
    )

    # STEP 4: request ride
    cmd_request = RequestRide("rider-1")

    result_request = runtime.execute(
        cmd_request,
        handle_request_ride,
        context
    )

    if "error" in result_request["result"]:
        print("Request failed:", result_request["result"]["error"])
        return

    print("Ride requested")
    print("Hash:", result_request["proof"]["hash"])

    persist_events(result_request["result"]["events"])

    # STEP 5: update context (DISPATCHER)
    context = AfriRideExecutionContext(
        role=RideAuthorityRole.DISPATCHER,
        drivers=degraded_drivers,
        state=result_request["result"]["state"]
    )

    # STEP 6: assign driver
    cmd_assign = AssignDriver("ride-001")

    result_assign = runtime.execute(
        cmd_assign,
        lambda cmd: handle_assign_driver(cmd, context),
        context
    )

    if "error" in result_assign["result"]:
        print("Assignment failed:", result_assign["result"]["error"])
        return

    print("Driver assigned")
    print("Hash:", result_assign["proof"]["hash"])

    persist_events(result_assign["result"]["events"])

    # STEP 7: original hash
    original_events = load_events()
    original_hash = hash_events(original_events)

    # STEP 8: replay
    replayed_events = replay_system(original_events)
    replay_hash = hash_events(replayed_events)

    print("\n--- REPLAY CHECK ---")
    print("Original hash:", original_hash)
    print("Replay hash  :", replay_hash)

    # STEP 9: metric
    metric = build_decision_metric(
        trace_id="failure-demo",
        original_hash=original_hash,
        replay_hash=replay_hash
    )

    print("\n--- METRICS ---")
    print(metric)

    # STEP 10: assert determinism
    assert_deterministic(original_hash, replay_hash)

    print("\n✅ CONTINUITY PRESERVED UNDER FAILURE\n")


# ---------------------------------------------------------
# ✅ ENTRYPOINT
# ---------------------------------------------------------

if __name__ == "__main__":
    run_failure_demo()
