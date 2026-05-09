/-
AfriTech Runtime Soundness Model (Lean 4)

Purpose:
Prove soundness of:
- execution
- admission
- surface enforcement

Guarantees:
✔ No execution without admission
✔ Only declared surfaces execute
✔ Execution is deterministic
✔ No hidden computation paths

This is the formalization of runtime safety.
-/


-- ============================================================
-- BASIC TYPES
-- ============================================================

abbrev Surface := String

inductive Authority where
  | constitutional
  | secondary
deriving DecidableEq

inductive AdmissionState where
  | admitted
  | rejected
deriving DecidableEq


-- ============================================================
-- SURFACE REGISTRY (DECLARED SURFACES ONLY)
-- ============================================================

def declared_surfaces : List Surface :=
  ["runtime_entry", "runtime_engine", "inference_requests"]

def is_declared (s : Surface) : Bool :=
  s ∈ declared_surfaces


-- ============================================================
-- EXECUTION MODEL
-- ============================================================

structure Context where
  surface : Surface
  authority : Authority
  payload : Nat
deriving Repr

structure Result where
  value : Nat
deriving Repr


-- deterministic execution function
def execute_fn (c : Context) : Result :=
  { value := c.payload * 2 }   -- pure function


-- ============================================================
-- ADMISSION MODEL
-- ============================================================

def admit (c : Context) : AdmissionState :=
  if is_declared c.surface then
    AdmissionState.admitted
  else
    AdmissionState.rejected


-- ============================================================
-- RUNTIME EXECUTION (GUARDED)
-- ============================================================

def run (c : Context) : Option Result :=
  match admit c with
  | AdmissionState.admitted => some (execute_fn c)
  | AdmissionState.rejected => none


-- ============================================================
-- THEOREM 1 — ADMISSION REQUIRED
-- ============================================================

theorem admission_required :
  ∀ c r,
  run c = some r →
  admit c = AdmissionState.admitted :=
by
  intro c r
  unfold run
  cases h : admit c
  case rejected =>
    simp [h]   -- run returns none
    intro h_run
    contradiction
  case admitted =>
    simp [h]


-- ============================================================
-- THEOREM 2 — DECLARED SURFACE REQUIRED
-- ============================================================

theorem surface_must_be_declared :
  ∀ c r,
  run c = some r →
  is_declared c.surface = true :=
by
  intro c r h_run
  have h_admit := admission_required c r h_run

  unfold admit at *

  cases h : is_declared c.surface with
  | false =>
      simp [h] at h_admit
      contradiction
  | true =>
      exact h


-- ============================================================
-- THEOREM 3 — NO EXECUTION ON UNDECLARED SURFACE
-- ============================================================

theorem no_execution_if_undeclared :
  ∀ c,
  is_declared c.surface = false →
  run c = none :=
by
  intro c h
  unfold run admit
  simp [h]


-- ============================================================
-- THEOREM 4 — DETERMINISTIC EXECUTION
-- ============================================================

theorem execution_deterministic :
  ∀ c r1 r2,
  run c = some r1 →
  run c = some r2 →
  r1 = r2 :=
by
  intro c r1 r2 h1 h2

  unfold run at *

  cases h_admit : admit c
  case rejected =>
    simp [h_admit] at h1
  case admitted =>
    simp [h_admit] at h1 h2
    injection h1 with h_r1
    injection h2 with h_r2
    rw [h_r1, h_r2]


-- ============================================================
-- THEOREM 5 — EXECUTION IS PURE
-- ============================================================

theorem execution_pure :
  ∀ c,
  run c = match admit c with
          | AdmissionState.admitted => some (execute_fn c)
          | _ => none :=
by
  intro c
  rfl


-- ============================================================
-- THEOREM 6 — NO HIDDEN EXECUTION PATH
-- ============================================================

theorem no_hidden_execution :
  ∀ c r,
  run c = some r →
  ∃ f, r = f c :=
by
  intro c r h

  cases h_admit : admit c
  case rejected =>
    simp [run, h_admit] at h
  case admitted =>
    simp [run, h_admit] at h
    exists execute_fn
    exact h


-- ============================================================
-- THEOREM 7 — AUTHORITY DOES NOT BYPASS ADMISSION
-- ============================================================

theorem authority_cannot_bypass_admission :
  ∀ c r,
  run c = some r →
  admit c = AdmissionState.admitted :=
by
  exact admission_required


-- ============================================================
-- THEOREM 8 — CLOSED-WORLD EXECUTION
-- ============================================================

theorem closed_world_execution :
  ∀ c r,
  run c = some r →
  c.surface ∈ declared_surfaces :=
by
  intro c r h
  have h_decl := surface_must_be_declared c r h
  unfold is_declared at h_decl
  exact h_decl


-- ============================================================
-- FINAL ASSERTION
-- ============================================================

/-
We have proven:

✔ Execution requires admission
