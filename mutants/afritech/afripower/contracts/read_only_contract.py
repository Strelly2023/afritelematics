"""
AFRIPower Read-Only Contract

Canonical non-authority contract for AFRIPower intelligence surfaces.

This contract governs all AFRIPower layers:
    - dashboard
    - AI reasoning
    - graph projection
    - graph query
    - enterprise intelligence display

─────────────────────────────────────────────────────────────────────
CONSTITUTIONAL LAW
─────────────────────────────────────────────────────────────────────

AFRIPower consumes authority.
AFRIPower does not create authority.

AFRIPower may:
    - observe
    - analyze
    - explain
    - represent

AFRIPower must NEVER:
    - execute runtime behavior
    - validate runtime truth
    - enforce governance
    - mutate receipts
    - mutate proof artifacts
    - create authority
    - determine admissibility
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

# =============================================================================
# CONTRACT STATUS
# =============================================================================

CONTRACT_STATUS = "READ_ONLY_INTELLIGENCE_CONTRACT"
CONTRACT_VERSION = "1.0"

# =============================================================================
# AUTHORITY FLAGS (ALL MUST REMAIN FALSE)
# =============================================================================

RUNTIME_AUTHORITY: bool = False
ENFORCEMENT_AUTHORITY: bool = False
VALIDATION_AUTHORITY: bool = False
GOVERNANCE_AUTHORITY: bool = False
INTELLIGENCE_AUTHORITY: bool = False

EXECUTION_AUTHORITY: bool = False
REPLAY_AUTHORITY: bool = False
PROOF_AUTHORITY: bool = False

AUTHORITATIVE: bool = False

# =============================================================================
# BEHAVIOR FLAGS (ALL TRUE = SAFE)
# =============================================================================

READ_ONLY: bool = True
DISPLAY_ONLY: bool = True
OBSERVATIONAL_ONLY: bool = True
INTERPRETIVE_ONLY: bool = True
REPRESENTATION_ONLY: bool = True

# =============================================================================
# LAW ASSERTIONS (TRUE = DECLARATIVE LAW)
# =============================================================================

LAW_AFRIPOWER_IS_READ_ONLY = True
LAW_AFRIPOWER_IS_NON_AUTHORITATIVE = True
LAW_AFRIPOWER_IS_DISPLAY_ONLY = True
LAW_AFRIPOWER_IS_OBSERVATIONAL_ONLY = True
LAW_AFRIPOWER_IS_INTERPRETIVE_ONLY = True
LAW_AFRIPOWER_IS_REPRESENTATION_ONLY = True

LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY = True
LAW_AFRIPOWER_CANNOT_EXECUTE = True
LAW_AFRIPOWER_CANNOT_VALIDATE = True
LAW_AFRIPOWER_CANNOT_ENFORCE = True
LAW_AFRIPOWER_CANNOT_MUTATE_RECEIPTS = True
LAW_AFRIPOWER_CANNOT_MUTATE_PROOF = True
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore

# =============================================================================
# CONTRACT MODEL
# =============================================================================


@dataclass(frozen=True)
class ReadOnlyContract:
    """
    Immutable non-authority contract for AFRIPower surfaces.

    This is:
        ✅ declarative
        ✅ structural
        ✅ validator-friendly

    This is NOT:
        ❌ runtime enforcement
        ❌ governance enforcement
        ❌ proof validation
    """

    # Authority flags
    runtime_authority: bool = RUNTIME_AUTHORITY
    enforcement_authority: bool = ENFORCEMENT_AUTHORITY
    validation_authority: bool = VALIDATION_AUTHORITY
    governance_authority: bool = GOVERNANCE_AUTHORITY
    intelligence_authority: bool = INTELLIGENCE_AUTHORITY

    execution_authority: bool = EXECUTION_AUTHORITY
    replay_authority: bool = REPLAY_AUTHORITY
    proof_authority: bool = PROOF_AUTHORITY

    # Behavioral guarantees
    read_only: bool = READ_ONLY
    display_only: bool = DISPLAY_ONLY
    observational_only: bool = OBSERVATIONAL_ONLY
    interpretive_only: bool = INTERPRETIVE_ONLY
    representation_only: bool = REPRESENTATION_ONLY

    # Authority state
    authoritative: bool = AUTHORITATIVE

    # Identity
    contract_status: str = CONTRACT_STATUS
    version: str = CONTRACT_VERSION

    # -----------------------------------------------------------------
    # Canonical Representation
    # -----------------------------------------------------------------

    def canonical_dict(self) -> Dict[str, object]:
        """Return canonical validator-friendly contract metadata."""

        return {
            "contract_status": self.contract_status,
            "version": self.version,

            # Authority
            "runtime_authority": self.runtime_authority,
            "enforcement_authority": self.enforcement_authority,
            "validation_authority": self.validation_authority,
            "governance_authority": self.governance_authority,
            "intelligence_authority": self.intelligence_authority,
            "execution_authority": self.execution_authority,
            "replay_authority": self.replay_authority,
            "proof_authority": self.proof_authority,

            # Behavior
            "read_only": self.read_only,
            "display_only": self.display_only,
            "observational_only": self.observational_only,
            "interpretive_only": self.interpretive_only,
            "representation_only": self.representation_only,

            # Authority state
            "authoritative": self.authoritative,

            # Law signals (for CI / audit)
            "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
            "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
            "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
            "law_observational_only": LAW_AFRIPOWER_IS_OBSERVATIONAL_ONLY,
            "law_interpretive_only": LAW_AFRIPOWER_IS_INTERPRETIVE_ONLY,
            "law_representation_only": LAW_AFRIPOWER_IS_REPRESENTATION_ONLY,
            "law_no_authority_creation": LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY,
        }


# =============================================================================
# DEFAULT INSTANCE
# =============================================================================

DEFAULT_READ_ONLY_CONTRACT = ReadOnlyContract()

# =============================================================================
# METADATA EXPORT
# =============================================================================


def read_only_contract_metadata() -> Dict[str, object]:
    """
    Return canonical AFRIPower read-only contract metadata.

    ✅ Pure
    ✅ Deterministic
    ✅ CI-safe
    """

    return DEFAULT_READ_ONLY_CONTRACT.canonical_dict()


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def assert_read_only_contract(contract: ReadOnlyContract) -> bool:
    args = [contract]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_assert_read_only_contract__mutmut_orig, x_assert_read_only_contract__mutmut_mutants, args, kwargs, None)


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_orig(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_1(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all(None)


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_2(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is not False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_3(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is True,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_4(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is not False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_5(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is True,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_6(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is not False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_7(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is True,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_8(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is not False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_9(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is True,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_10(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is not False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_11(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is True,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_12(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is not False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_13(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is True,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_14(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is not False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_15(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is True,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_16(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is not False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_17(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is True,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_18(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is not True,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_19(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is False,
        contract.display_only is True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_20(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is not True,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_21(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is False,
        contract.authoritative is False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_22(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is not False,
    ])


# =============================================================================
# VALIDATION HELPER (STRUCTURAL ONLY)
# =============================================================================


def x_assert_read_only_contract__mutmut_23(contract: ReadOnlyContract) -> bool:
    """
    Structural assertion helper.

    ✅ Checks non-authority conditions
    ❌ Does NOT validate runtime truth
    ❌ Does NOT enforce governance

    Safe for:
        - CI validation
        - schema checks
        - audit verification
    """

    return all([
        contract.runtime_authority is False,
        contract.enforcement_authority is False,
        contract.validation_authority is False,
        contract.governance_authority is False,
        contract.intelligence_authority is False,
        contract.execution_authority is False,
        contract.replay_authority is False,
        contract.proof_authority is False,
        contract.read_only is True,
        contract.display_only is True,
        contract.authoritative is True,
    ])

x_assert_read_only_contract__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_assert_read_only_contract__mutmut_1': x_assert_read_only_contract__mutmut_1, 
    'x_assert_read_only_contract__mutmut_2': x_assert_read_only_contract__mutmut_2, 
    'x_assert_read_only_contract__mutmut_3': x_assert_read_only_contract__mutmut_3, 
    'x_assert_read_only_contract__mutmut_4': x_assert_read_only_contract__mutmut_4, 
    'x_assert_read_only_contract__mutmut_5': x_assert_read_only_contract__mutmut_5, 
    'x_assert_read_only_contract__mutmut_6': x_assert_read_only_contract__mutmut_6, 
    'x_assert_read_only_contract__mutmut_7': x_assert_read_only_contract__mutmut_7, 
    'x_assert_read_only_contract__mutmut_8': x_assert_read_only_contract__mutmut_8, 
    'x_assert_read_only_contract__mutmut_9': x_assert_read_only_contract__mutmut_9, 
    'x_assert_read_only_contract__mutmut_10': x_assert_read_only_contract__mutmut_10, 
    'x_assert_read_only_contract__mutmut_11': x_assert_read_only_contract__mutmut_11, 
    'x_assert_read_only_contract__mutmut_12': x_assert_read_only_contract__mutmut_12, 
    'x_assert_read_only_contract__mutmut_13': x_assert_read_only_contract__mutmut_13, 
    'x_assert_read_only_contract__mutmut_14': x_assert_read_only_contract__mutmut_14, 
    'x_assert_read_only_contract__mutmut_15': x_assert_read_only_contract__mutmut_15, 
    'x_assert_read_only_contract__mutmut_16': x_assert_read_only_contract__mutmut_16, 
    'x_assert_read_only_contract__mutmut_17': x_assert_read_only_contract__mutmut_17, 
    'x_assert_read_only_contract__mutmut_18': x_assert_read_only_contract__mutmut_18, 
    'x_assert_read_only_contract__mutmut_19': x_assert_read_only_contract__mutmut_19, 
    'x_assert_read_only_contract__mutmut_20': x_assert_read_only_contract__mutmut_20, 
    'x_assert_read_only_contract__mutmut_21': x_assert_read_only_contract__mutmut_21, 
    'x_assert_read_only_contract__mutmut_22': x_assert_read_only_contract__mutmut_22, 
    'x_assert_read_only_contract__mutmut_23': x_assert_read_only_contract__mutmut_23
}
x_assert_read_only_contract__mutmut_orig.__name__ = 'x_assert_read_only_contract'


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def enforce_read_only_contract(contract: ReadOnlyContract) -> None:
    args = [contract]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_enforce_read_only_contract__mutmut_orig, x_enforce_read_only_contract__mutmut_mutants, args, kwargs, None)


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def x_enforce_read_only_contract__mutmut_orig(contract: ReadOnlyContract) -> None:
    """
    Strict assertion (raises on violation).

    Intended for CI / validator usage only.
    """

    if not assert_read_only_contract(contract):
        raise RuntimeError("AFRIPower ReadOnlyContract violation detected")


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def x_enforce_read_only_contract__mutmut_1(contract: ReadOnlyContract) -> None:
    """
    Strict assertion (raises on violation).

    Intended for CI / validator usage only.
    """

    if assert_read_only_contract(contract):
        raise RuntimeError("AFRIPower ReadOnlyContract violation detected")


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def x_enforce_read_only_contract__mutmut_2(contract: ReadOnlyContract) -> None:
    """
    Strict assertion (raises on violation).

    Intended for CI / validator usage only.
    """

    if not assert_read_only_contract(None):
        raise RuntimeError("AFRIPower ReadOnlyContract violation detected")


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def x_enforce_read_only_contract__mutmut_3(contract: ReadOnlyContract) -> None:
    """
    Strict assertion (raises on violation).

    Intended for CI / validator usage only.
    """

    if not assert_read_only_contract(contract):
        raise RuntimeError(None)


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def x_enforce_read_only_contract__mutmut_4(contract: ReadOnlyContract) -> None:
    """
    Strict assertion (raises on violation).

    Intended for CI / validator usage only.
    """

    if not assert_read_only_contract(contract):
        raise RuntimeError("XXAFRIPower ReadOnlyContract violation detectedXX")


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def x_enforce_read_only_contract__mutmut_5(contract: ReadOnlyContract) -> None:
    """
    Strict assertion (raises on violation).

    Intended for CI / validator usage only.
    """

    if not assert_read_only_contract(contract):
        raise RuntimeError("afripower readonlycontract violation detected")


# =============================================================================
# STRICT VALIDATOR ASSERT (OPTIONAL CI USE)
# =============================================================================


def x_enforce_read_only_contract__mutmut_6(contract: ReadOnlyContract) -> None:
    """
    Strict assertion (raises on violation).

    Intended for CI / validator usage only.
    """

    if not assert_read_only_contract(contract):
        raise RuntimeError("AFRIPOWER READONLYCONTRACT VIOLATION DETECTED")

x_enforce_read_only_contract__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_enforce_read_only_contract__mutmut_1': x_enforce_read_only_contract__mutmut_1, 
    'x_enforce_read_only_contract__mutmut_2': x_enforce_read_only_contract__mutmut_2, 
    'x_enforce_read_only_contract__mutmut_3': x_enforce_read_only_contract__mutmut_3, 
    'x_enforce_read_only_contract__mutmut_4': x_enforce_read_only_contract__mutmut_4, 
    'x_enforce_read_only_contract__mutmut_5': x_enforce_read_only_contract__mutmut_5, 
    'x_enforce_read_only_contract__mutmut_6': x_enforce_read_only_contract__mutmut_6
}
x_enforce_read_only_contract__mutmut_orig.__name__ = 'x_enforce_read_only_contract'


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    "ReadOnlyContract",
    "DEFAULT_READ_ONLY_CONTRACT",
    "read_only_contract_metadata",
    "assert_read_only_contract",
    "enforce_read_only_contract",

    # status
    "CONTRACT_STATUS",
    "CONTRACT_VERSION",

    # flags
    "READ_ONLY",
    "DISPLAY_ONLY",
    "OBSERVATIONAL_ONLY",
    "INTERPRETIVE_ONLY",
    "REPRESENTATION_ONLY",
]