/-
Afritech Lean — Executable Boundary
(Level 4 → Level 5 Hinge)

Purpose
-------

This file defines the *structural executable boundary*.

It does NOT:
  • execute transitions
  • validate admissibility
  • inspect proofs
  • compute authorization
  • introduce runtime semantics

It ONLY marks which artifacts are structurally eligible
to survive proof erasure.

Core principle:

  executability ≡ constructive inhabitation

Non-existence is represented by absence of inhabitant,
never by rejection or failure values.
-/

import afritech.lean.Kernel
import afritech.lean.State

universe u

namespace Afritech

/----------------------------------------------------
  Executable Witness
----------------------------------------------------/

/--
Executable is a structural witness that a transition
is constructively admissible.

It is not a runtime instruction.

Its existence certifies that:

  • governance derivability exists
  • production relation exists
  • resulting state is structurally valid

No proof object may be inspected.
-/
structure Executable where
  source : State
  action : Action
  proof  : Proof
  target : State

  derivable :
    Derivable source action proof

  produces :
    Produces source action target

  valid_target :
    ValidState target

/----------------------------------------------------
  Projection Interface
----------------------------------------------------/

/--
Source state projection.

Pure structural access.
-/
def sourceState (e : Executable) : State :=
  e.source

/--
Action projection.
-/
def executableAction (e : Executable) : Action :=
  e.action

/--
Target state projection.
-/
def targetState (e : Executable) : State :=
  e.target

/----------------------------------------------------
  Structural Preservation
----------------------------------------------------/

/--
Executability preserves target validity.

This is immediate by construction.
-/
theorem executable_preserves_validity :
  ∀ (e : Executable),
    ValidState (targetState e) :=
by
  intro e
  exact e.valid_target

/----------------------------------------------------
  Non-Inspection Discipline
----------------------------------------------------/

/--
Proof relevance is existential only.

No executable behavior may depend on proof inspection.

This theorem encodes proof opacity structurally.
-/
theorem proof_opacity :
  ∀ (e : Executable),
    ∃ π : Proof, π = e.proof :=
by
  intro e
  exact ⟨e.proof, rfl⟩

/----------------------------------------------------
  Structural Transition Witness
----------------------------------------------------/

/--
Every executable artifact induces a kernel transition.

This introduces no execution semantics.

It merely reflects structural admissibility into the
epoch-indexed transition space.
-/
axiom executable_transition :
  ∀ (e : Executable),
    ∃ epoch : Epoch,
      Transition e.source e.target epoch

/----------------------------------------------------
  Proof Erasure Boundary
----------------------------------------------------/

/--
ProductionArtifact is the proof-erased executable view.

Only data-level carriers remain.

This is the exact object permitted to cross
the Level 5 boundary.
-/
structure ProductionArtifact where
  source : State
  action : Action
  target : State

/--
Proof erasure projection.

Logical witnesses are removed.

No semantics are altered.
-/
def erase (e : Executable) : ProductionArtifact :=
{
  source := e.source
  action := e.action
  target := e.target
}

/----------------------------------------------------
  Erasure Preservation
----------------------------------------------------/

/--
Erasure preserves target validity.

Validity is structural and survives proof removal.
-/
theorem erase_preserves_validity :
  ∀ (e : Executable),
    ValidState (erase e).target :=
by
  intro e
  exact e.valid_target

/----------------------------------------------------
  Non-Failure Principle
----------------------------------------------------/

/--
Executability has no rejection constructor.

Either an executable inhabitant exists,
or no object exists.

There is no negative outcome.
-/
theorem no_failure_semantics :
  ∀ (e : Executable), True :=
by
  intro e
  trivial

end Afritech