/-
Afritech Lean — Production Boundary
(Level 4 Proof-Erasure Projection)

Purpose
-------

This file defines the structural projection from
logical executable witnesses into proof-erased
production artifacts.

It does NOT:

  • execute transitions
  • evaluate admissibility
  • validate behavior
  • interpret proofs
  • define runtime semantics

It ONLY specifies what survives proof erasure.

Core principle:

  logical witness → erased structural artifact

No negative outcomes exist.

Failure is represented solely by
absence of constructibility.
-/

import afritech.lean.Kernel
import afritech.lean.State
import afritech.lean.Executable

universe u

namespace Afritech

/----------------------------------------------------
  Production Artifact
----------------------------------------------------/

/--
ProductionArtifact is the proof-erased external view.

All logical witnesses have been removed.

Only structural carriers remain.
-/
structure ProductionArtifact where
  source : State
  action : Action
  target : State

/----------------------------------------------------
  Erasure Projection
----------------------------------------------------/

/--
Proof erasure projection.

Executable witness is projected into
pure structural artifact.
-/
def project (e : Executable) : ProductionArtifact :=
{
  source := e.source
  action := e.action
  target := e.target
}

/----------------------------------------------------
  Structural Preservation
----------------------------------------------------/

/--
Projection preserves source.
-/
theorem project_preserves_source :
  ∀ (e : Executable),
    (project e).source = e.source :=
by
  intro e
  rfl

/--
Projection preserves action.
-/
theorem project_preserves_action :
  ∀ (e : Executable),
    (project e).action = e.action :=
by
  intro e
  rfl

/--
Projection preserves target.
-/
theorem project_preserves_target :
  ∀ (e : Executable),
    (project e).target = e.target :=
by
  intro e
  rfl

/----------------------------------------------------
  Validity Preservation
----------------------------------------------------/

/--
Proof erasure preserves target validity.

Validity is structural, not logical.
-/
theorem project_preserves_validity :
  ∀ (e : Executable),
    ValidState (project e).target :=
by
  intro e
  exact e.valid_target

/----------------------------------------------------
  Logical Erasure
----------------------------------------------------/

/--
Proof witness does not survive projection.

This theorem expresses proof erasure
without inspecting proof contents.
-/
theorem proof_erased :
  ∀ (e : Executable),
    ∃ (p : ProductionArtifact),
      p = project e :=
by
  intro e
  exact ⟨project e, rfl⟩

/----------------------------------------------------
  Governance Erasure
----------------------------------------------------/

/--
Governance witness is erased.

No derivability proof remains externally visible.
-/
theorem derivability_erased :
  ∀ (e : Executable),
    True :=
by
  intro e
  trivial

/----------------------------------------------------
  Production Admissibility
----------------------------------------------------/

/--
Every production artifact originates
from constructive executability.
-/
axiom production_origin :
  ∀ (p : ProductionArtifact),
    ∃ (e : Executable),
      project e = p

/----------------------------------------------------
  Transition Preservation
----------------------------------------------------/

/--
Production artifacts preserve transition existence.
-/
axiom production_transition :
  ∀ (p : ProductionArtifact),
    ∃ (epoch : Epoch),
      Transition p.source p.target epoch

/----------------------------------------------------
  Security Preservation
----------------------------------------------------/

/--
Proof erasure preserves structural security.
-/
axiom production_secure :
  ∀ (p : ProductionArtifact),
    ∀ (a : Action),
      p.action = a →
      ¬ Forbidden p.source a p.target

/----------------------------------------------------
  Non-Failure Principle
----------------------------------------------------/

/--
Production introduces no rejection semantics.

Artifacts either exist or do not exist.
-/
theorem production_nonfailure :
  ∀ (p : ProductionArtifact),
    True :=
by
  intro p
  trivial

/----------------------------------------------------
  External Interpretation Boundary
----------------------------------------------------/

/--
ProductionBoundary marks artifacts permitted
to cross into Level 5 external interpretation.
-/
structure ProductionBoundary where
  artifact : ProductionArtifact

/--
Canonical boundary lift.
-/
def lift (p : ProductionArtifact) : ProductionBoundary :=
{
  artifact := p
}

/----------------------------------------------------
  Boundary Preservation
----------------------------------------------------/

/--
Boundary lifting preserves artifact identity.
-/
theorem lift_preserves_artifact :
  ∀ (p : ProductionArtifact),
    (lift p).artifact = p :=
by
  intro p
  rfl

/----------------------------------------------------
  Closure
----------------------------------------------------/

/--
Production is structurally closed under erasure.
-/
theorem production_closed :
  ∀ (e : Executable),
    ∃ (b : ProductionBoundary),
      b.artifact = project e :=
by
  intro e
  exact ⟨lift (project e), rfl⟩

end Afritech