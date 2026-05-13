from ecosystems.afriride.core.constitutional.runtime import (
    ExecutionRuntime,
    RuntimeAdmissionEngine
)

from ecosystems.afriride.core.constitutional.ride_guards import ALL_GUARDS

runtime = ExecutionRuntime(
    RuntimeAdmissionEngine(guards=ALL_GUARDS)
)


def execute_command(command, handler, context):
    return runtime.execute(command, handler, context)
