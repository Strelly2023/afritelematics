from __future__ import annotations

from afritech.core_platform.adaptive_sla import AdaptiveSLAController, TrafficPredictor, adaptive_sla_limit


class MemoryRedis:
    def __init__(self) -> None:
        self.strings: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        self.strings[key] = value

    def get(self, key: str):
        return self.strings.get(key)

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.strings.pop(key, None)


def test_predictor_ema_moves_toward_new_observations() -> None:
    predictor = TrafficPredictor(alpha=0.3)

    first = predictor.update(100)
    second = predictor.update(160)

    assert first == 100
    assert second > first
    assert predictor.samples == 2


def test_adaptive_sla_limit_expands_then_contracts() -> None:
    expanded, reason_expand = adaptive_sla_limit(100, 50, "enterprise")
    contracted, reason_contract = adaptive_sla_limit(100, 180, "enterprise")

    assert expanded == 120
    assert reason_expand == "burst_room_for_expected_headroom"
    assert contracted == 50
    assert reason_contract == "protective_contraction"


def test_controller_persists_prediction_and_flags_anomaly() -> None:
    controller = AdaptiveSLAController(client=MemoryRedis(), region="AU", default_limit=100)

    first = controller.observe(
        "org-ai",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=40,
        observed_at=1000.0,
    )
    second = controller.recommend(
        "org-ai",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=40,
    )
    anomaly = controller.observe(
        "org-ai",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=180,
        errors=5,
        observed_at=1060.0,
    )

    assert first["mode"] == "predictive"
    assert second["mode"] == "predictive"
    assert second["adjusted_limit"] >= 100
    assert anomaly["anomaly"] is True
    assert anomaly["action"] == "throttle"
    assert anomaly["adjusted_limit"] < 100


def test_controller_keeps_cold_start_limits_stable() -> None:
    controller = AdaptiveSLAController(client=MemoryRedis(), region="AU", default_limit=100)

    recommendation = controller.recommend(
        "org-cold",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=180,
    )

    assert recommendation["adjusted_limit"] == 100
    assert recommendation["policy"]["reason"] == "cold_start_stable_limit"
    assert recommendation["prediction"]["confidence"] == 0.05


def test_controller_regulator_override_ignores_prediction_and_latency() -> None:
    controller = AdaptiveSLAController(client=MemoryRedis(), region="AU", default_limit=100)

    controller.observe(
        "org-regulator",
        trust_level="regulator",
        base_limit=100,
        region="AU",
        latency_ms=200,
        observed_at=1000.0,
    )
    recommendation = controller.recommend(
        "org-regulator",
        trust_level="regulator",
        base_limit=100,
        region="AU",
        latency_ms=240,
        load_hint=999.0,
    )

    assert recommendation["adjusted_limit"] == 100
    assert recommendation["policy"]["reason"] == "regulatory_override"


def test_controller_smooths_latency_and_reflects_error_ratio() -> None:
    controller = AdaptiveSLAController(client=MemoryRedis(), region="AU", default_limit=100)

    first = controller.observe(
        "org-latency",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=20,
        observed_at=1000.0,
    )
    second = controller.observe(
        "org-latency",
        trust_level="enterprise",
        base_limit=100,
        region="AU",
        latency_ms=200,
        observed_at=1060.0,
    )

    assert first["smoothed_latency_ms"] == 20
    assert second["smoothed_latency_ms"] < 200
    assert 0.05 <= second["prediction"]["confidence"] <= 0.99
