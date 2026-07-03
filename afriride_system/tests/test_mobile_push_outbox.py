from afriride_system.backend.api_gateway.gateway import build_gateway
from afriride_system.backend.repositories import PushOutboxRepository
from afriride_system.backend.storage import AfriRideStorage
from afriride_system.workers.mobile_push_worker import MobilePushWorker


def test_outbox_enqueue_is_idempotent_and_worker_delivers_once(tmp_path) -> None:
    repository = PushOutboxRepository(AfriRideStorage(tmp_path / "outbox.sqlite3"))
    first = repository.enqueue(
        "rider-1", "driver_assigned", {"ride_id": "ride-1"},
        idempotency_key="ride:ride-1:driver_assigned",
    )
    second = repository.enqueue(
        "rider-1", "driver_assigned", {"ride_id": "ride-1"},
        idempotency_key="ride:ride-1:driver_assigned",
    )
    delivered = []
    result = MobilePushWorker(
        repository, lambda actor, event, payload: delivered.append((actor, event, payload))
    ).run_once()
    assert first == second
    assert result == {"delivered": 1, "failed": 0}
    assert len(delivered) == 1
    assert repository.get(first)["status"] == "delivered"
    assert MobilePushWorker(repository, lambda *_: None).run_once()["delivered"] == 0


def test_outbox_failure_records_attempt_and_terminal_status(tmp_path) -> None:
    repository = PushOutboxRepository(AfriRideStorage(tmp_path / "retry.sqlite3"))
    outbox_id = repository.enqueue(
        "rider-1", "ride_update", {}, idempotency_key="retry-1"
    )
    repository.mark_failed(outbox_id, "provider_down", max_attempts=1)
    record = repository.get(outbox_id)
    assert record["status"] == "failed"
    assert record["delivery_attempt"] == 1
    assert record["last_error"] == "provider_down"


def test_outbox_claim_prevents_duplicate_workers(tmp_path) -> None:
    storage = AfriRideStorage(tmp_path / "claim.sqlite3")
    first_worker = PushOutboxRepository(storage)
    second_worker = PushOutboxRepository(storage)
    first_worker.enqueue("rider-1", "ride_update", {}, idempotency_key="claim-1")
    assert len(first_worker.claim_pending()) == 1
    assert second_worker.claim_pending() == ()


def test_driver_assignment_commits_business_state_and_push_outbox(tmp_path) -> None:
    gateway = build_gateway(db_path=tmp_path / "atomic.sqlite3", reset=True)
    gateway.driver.status({"driver_id": "driver-1", "online": True})
    ride = gateway.passenger.request_ride(
        {"ride_id": "ride-1", "passenger_id": "rider-1", "pickup": "A", "destination": "B"}
    )
    gateway.driver.accept({"driver_id": "driver-1", "ride_id": ride["ride_id"]})
    assert gateway.dispatcher.ride_status("ride-1")["status"] == "DRIVER_ASSIGNED"
    pending = gateway.push_outbox_repository.pending()
    assert len(pending) == 1
    assert pending[0]["idempotency_key"] == "ride:ride-1:driver_assigned"
