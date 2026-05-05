/-
Afritech Kernel — Core Object Theory (Canonical Level 4)

This file encodes the frozen Level 2 Afritech formal system
as a pure relational type-theoretic kernel.

Properties:
  • non-computational
  • non-reflective
  • no runtime semantics
  • no decision procedures
  • no operational interpretation

Everything here is structural.

The kernel defines:
  • ontological carriers
  • governance relations
  • transition relations
  • security exclusion constraints
  • epoch ordering structure
  • structural coherence axioms
-/

universe u

namespace Afritech

/====================================================
  Core Ontological Carriers
====================================================/

/--
Abstract system state.

Opaque by construction:
no inspection, no decomposition, no computation.
-/
opaque State : Type u

/--
Abstract governance action.

Actions are structural inputs only.
No operational semantics are attached.
-/
opaque Action : Type u

/--
Abstract proof witness.

Proof objects certify admissibility structurally.
They are never inspected or evaluated.
-/
opaque Proof : Type u

/--
Abstract epoch carrier.

Epochs define ordering only.
They are not temporal values.
-/
opaque Epoch : Type u


/====================================================
  Epoch Ordering Structure
====================================================/

/--
Primitive strict ordering over epochs.
-/
constant epoch_lt : Epoch → Epoch → Prop

/--
Irreflexivity of epoch ordering.
-/
axiom epoch_irrefl :
  ∀ e : Epoch,
    ¬ epoch_lt e e

/--
Transitivity of epoch ordering.
-/
axiom epoch_trans :
  ∀ e₁ e₂ e₃ : Epoch,
    epoch_lt e₁ e₂ →
    epoch_lt e₂ e₃ →
    epoch_lt e₁ e₃

/--
Totality over distinct epochs.
-/
axiom epoch_total :
  ∀ e₁ e₂ : Epoch,
    e₁ ≠ e₂ →
    epoch_lt e₁ e₂ ∨ epoch_lt e₂ e₁


/====================================================
  Core Relations
====================================================/

/--
Governance relation.

Derivable s a π means:
proof witness π certifies action a
as admissible from state s.
-/
constant Derivable :
  State → Action → Proof → Prop

/--
Structural production relation.

Produces s a s' means:
action a structurally relates
state s to state s'.
-/
constant Produces :
  State → Action → State → Prop

/--
Epoch-indexed transition relation.

Transition is primitive and relational.
It is not computed.
-/
constant Transition :
  State → State → Epoch → Prop

/--
Security exclusion relation.

Forbidden s a s' means:
the structural transition is excluded.
-/
constant Forbidden :
  State → Action → State → Prop


/====================================================
  Structural Soundness
====================================================/

/--
Every transition admits some governance witness
and some production witness.

No uniqueness is implied.
No computational interpretation exists.
-/
axiom admissibility_sound :
  ∀ s s' e,
    Transition s s' e →
    ∃ a π s'',
      Derivable s a π ∧
      Produces s a s''

/--
Every transition is structurally anchored
to some production relation.
-/
axiom transition_has_production :
  ∀ s s' e,
    Transition s s' e →
    ∃ a,
      Produces s a s'


/====================================================
  Epoch Monotonicity
====================================================/

/--
Transitions never regress in epoch ordering.
-/
axiom epoch_monotone :
  ∀ s₁ s₂ s₃ e₁ e₂,
    Transition s₁ s₂ e₁ →
    Transition s₂ s₃ e₂ →
    ¬ epoch_lt e₂ e₁


/====================================================
  Security Orthogonality
====================================================/

/--
Security constrains production
without altering governance derivability.
-/
axiom security_filters_production :
  ∀ s a s',
    Produces s a s' →
    ¬ Forbidden s a s'


/====================================================
  Kernel Consistency
====================================================/

/--
Governance witnesses are structurally coherent.

This encodes Level 3 consistency.
-/
constant Incompatible :
  Proof → Proof → Prop

axiom governance_consistency :
  ∀ s a π₁ π₂,
    Derivable s a π₁ →
    Derivable s a π₂ →
    ¬ Incompatible π₁ π₂


/====================================================
  Kernel Bundle
====================================================/

/--
Pure structural aggregation.

No execution semantics.
No interpretation semantics.
No computation.
-/
structure Kernel where
  S : Type u
  A : Type u
  Π : Type u
  E : Type u

  derivable :
    S → A → Π → Prop

  produces :
    S → A → S → Prop

  transition :
    S → S → E → Prop

end Afritech