from __future__ import annotations

from afritech.simulation.distributed.message_scheduler import MessageScheduler
from afritech.simulation.distributed.network_model import NetworkModel
from afritech.simulation.distributed.network_trace import NetworkTrace


def _messages(count: int = 20) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "id": f"m{index:03d}",
            "timestamp": index,
            "request_id": f"req-{index:03d}",
            "city_id": f"city-{index % 3}",
        }
        for index in range(count)
    )


def test_network_determinism() -> None:
    model = NetworkModel(seed=42)
    messages = _messages()

    r1 = model.transmit(messages)
    r2 = model.transmit(messages)

    assert r1 == r2
    assert model.trace_hash(messages) == model.trace_hash(messages)


def test_network_determinism_is_independent_of_input_order() -> None:
    model = NetworkModel(seed=42)
    scheduler = MessageScheduler()
    messages = _messages()

    forward = model.transmit(scheduler.schedule(messages))
    reversed_delivery = model.transmit(scheduler.schedule(reversed(messages)))

    assert forward == reversed_delivery
    assert NetworkTrace.hash_trace(forward) == NetworkTrace.hash_trace(reversed_delivery)


def test_network_seed_changes_trace_but_remains_stable() -> None:
    messages = _messages()
    model_a = NetworkModel(seed=42)
    model_b = NetworkModel(seed=99)

    assert model_a.trace(messages) == model_a.trace(messages)
    assert model_b.trace(messages) == model_b.trace(messages)
    assert model_a.trace(messages) != model_b.trace(messages)
