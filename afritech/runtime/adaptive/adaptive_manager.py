"""
AfriTech Adaptive Manager

PURPOSE:
--------
Central orchestration layer for runtime optimization (HOW).

Responsibilities:
- collect telemetry
- analyze system state
- generate safe policy adaptations
- enforce guard constraints
- coordinate adaptive decision pipeline

CRITICAL LAW:
-------------
Adaptive Manager MAY:
- optimize execution parameters (batch size, retries)
- respond to load conditions
- tune runtime performance

Adaptive Manager may NOT:
- modify event data
- alter execution semantics
- interfere with replay truth
"""

from afritech.runtime.adaptive.telemetry_collector import collect_telemetry
from afritech.runtime.adaptive.load_analyzer import analyze_load
from afritech.runtime.adaptive.policy_optimizer import optimize_policy
from afritech.runtime.adaptive.adaptation_engine import apply_adaptation
from afritech.runtime.adaptive.strategy_registry import get_strategy
from afritech.runtime.guards import enforce_adaptive_limits


# ============================================================
# ✅ ADAPTIVE MANAGER CLASS
# ============================================================

class AdaptiveManager:
    """
    Coordinates adaptive runtime optimization.

    Acts as the "brain" of the adaptive layer.
    """

    def __init__(self, strategy: str = "default"):
        self.strategy = strategy

    # ========================================================
    # ✅ MAIN EVALUATION PIPELINE
    # ========================================================

    def evaluate(self, context):
        """
        Main adaptive evaluation loop.

        Steps:
        1. Collect runtime telemetry
        2. Analyze load conditions
        3. Select optimization strategy
        4. Generate policy changes
        5. Enforce guard safety
        6. Apply adaptation safely
        """

        # ----------------------------------------------------
        # 1. Collect telemetry
        # ----------------------------------------------------
        telemetry = collect_telemetry(context)

        # ----------------------------------------------------
        # 2. Analyze system load
        # ----------------------------------------------------
        load_state = analyze_load(telemetry)

        # ----------------------------------------------------
        # 3. Resolve strategy
        # ----------------------------------------------------
        strategy_fn = get_strategy(self.strategy)

        if strategy_fn:
            proposed_policy = strategy_fn(load_state, context)
        else:
            # fallback to default optimizer
            proposed_policy = optimize_policy(load_state, context)

        # ----------------------------------------------------
        # 4. Enforce guard constraints
        # ----------------------------------------------------
        enforce_adaptive_limits(proposed_policy)

        # ----------------------------------------------------
        # 5. Apply adaptation
        # ----------------------------------------------------
        updated_policy = apply_adaptation(context, proposed_policy)

        # ----------------------------------------------------
        # 6. Return structured result
        # ----------------------------------------------------
        return {
            "load_state": load_state,
            "applied_policy": updated_policy,
            "strategy": self.strategy,
        }

    # ========================================================
    # ✅ EVALUATE WITHOUT APPLYING (DRY RUN)
    # ========================================================

    def dry_run(self, context):
        """
        Simulates adaptation WITHOUT applying changes.

        Useful for:
        - testing
        - monitoring
        - debugging
        """

        telemetry = collect_telemetry(context)
        load_state = analyze_load(telemetry)

        strategy_fn = get_strategy(self.strategy)

        if strategy_fn:
            proposed_policy = strategy_fn(load_state, context)
        else:
            proposed_policy = optimize_policy(load_state, context)

        enforce_adaptive_limits(proposed_policy)

        return {
            "load_state": load_state,
            "proposed_policy": proposed_policy,
            "strategy": self.strategy,
        }

    # ========================================================
    # ✅ TELEMETRY VIEW
    # ========================================================

    def get_telemetry(self, context):
        """
        Expose runtime telemetry (read-only).
        """

        return collect_telemetry(context)

    # ========================================================
    # ✅ LOAD STATE ONLY
    # ========================================================

    def get_load_state(self, context):
        """
        Quick load state check without full adaptation.
        """

        telemetry = collect_telemetry(context)
        return analyze_load(telemetry)

    # ========================================================
    # ✅ STRATEGY SWITCHING
    # ========================================================

    def set_strategy(self, strategy_name: str):
        """
        Change adaptive strategy at runtime.
        """

        self.strategy = strategy_name

    # ========================================================
    # ✅ TRACE (OBSERVABILITY)
    # ========================================================

    def trace_decision(self, context):
        """
        Debug-friendly trace of adaptive decision flow.

        Does NOT modify system state.
        """

        telemetry = collect_telemetry(context)
        load_state = analyze_load(telemetry)

        strategy_fn = get_strategy(self.strategy)

        if strategy_fn:
            proposed_policy = strategy_fn(load_state, context)
        else:
            proposed_policy = optimize_policy(load_state, context)

        return {
            "telemetry": telemetry,
            "load_state": load_state,
            "strategy": self.strategy,
            "proposed_policy": proposed_policy,
        }