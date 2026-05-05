/-
Afritech Kernel — State Layer (Corrected Canonical Version)

This layer defines the structural interface of system states.

Key invariants:
  • State is an opaque kernel carrier type (defined in Kernel)
  • Validity is structural (constructibility via embed)
  • All states arise from kernel embeddings (state_totality)
  • No runtime validation semantics exist

Ontology:
  existence ≡ image of embed
  validity  ≡ membership in embedding image
-/

import afritech.lean.Kernel
import afritech.lean.Production

universe u

namespace Afritech

/--
Concrete generator space of states.
This exists only as a structural source for embeddings.
-/
constant ConcreteState : Type u

/--
Embedding from concrete structure into kernel state space.

State itself is defined in Kernel.lean and is NOT redeclared here.
-/
constant embed : ConcreteState → State

/--
ValidState is a structural predicate:
a state is valid iff it arises from kernel embedding.
-/
inductive ValidState : State → Prop
| intro :
    ∀ (cs : ConcreteState),
      ValidState (embed cs)

/--
Axiom: every State is representable via embedding.
This enforces surjectivity of the kernel embedding.
-/
axiom state_totality :
  ∀ (s : State), ∃ (cs : ConcreteState), s = embed cs

/--
Validity is preserved under equality of states.
-/
theorem validity_respects_eq :
  ∀ {s1 s2 : State},
    s1 = s2 →
    ValidState s1 →
    ValidState s2 :=
by
  intro s1 s2 h hv
  subst h
  exact hv

/--
All states are valid (derived structural theorem).

This is a consequence of kernel surjectivity:
every state is in the image of embed.
-/
theorem all_states_valid :
  ∀ (s : State), ValidState s :=
by
  intro s
  obtain ⟨cs, hcs⟩ := state_totality s
  subst hcs
  exact ValidState.intro cs

end Afritech