from afritech.ci import binding_completeness_validator
from afritech.ci import execution_completeness_validator
from afritech.ci import formal_runtime_equivalence_validator
from afritech.ci import full_witness_coverage_validator
from afritech.ci import registry_completeness_validator
from afritech.ci import surface_state_resolution_validator


def test_l15_completion_validators_pass() -> None:
    registry_completeness_validator.validate()
    surface_state_resolution_validator.validate()
    binding_completeness_validator.validate()
    execution_completeness_validator.validate()
    full_witness_coverage_validator.validate()
    formal_runtime_equivalence_validator.validate()
