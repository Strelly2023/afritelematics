from ecosystems.afriride.runtime.commands import AssignDriver
from ecosystems.afriride.runtime.deterministic_executor import DeterministicExecutor
from ecosystems.afriride.runtime.state import RideState


def test_duplicate_assign_driver_behavior():

    state = RideState(
        drivers_available={"A"},
        ride_status="OPEN",
    )

    commands = [
        AssignDriver("A"),
        AssignDriver("A"),
    ]

    trace = DeterministicExecutor.execute(state, commands)

    print("\nTRACE:", trace)
