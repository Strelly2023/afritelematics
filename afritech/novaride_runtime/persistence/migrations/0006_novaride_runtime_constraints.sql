ALTER TABLE mobility_events
    ADD CONSTRAINT mobility_events_integrity_hash_not_empty
    CHECK (length(integrity_hash) > 10);

ALTER TABLE idempotency_records
    ADD CONSTRAINT idempotency_command_hash_not_empty
    CHECK (length(command_hash) > 10);

ALTER TABLE bookings
    ADD CONSTRAINT bookings_state_valid
    CHECK (state IN ('DRAFT','QUOTED','CONFIRMED','SEARCHING','ASSIGNED','CANCELLED','EXPIRED','CONVERTED_TO_TRIP'));

ALTER TABLE trips
    ADD CONSTRAINT trips_state_valid
    CHECK (lifecycle_state IN ('CREATED','MATCHING','ASSIGNED','DRIVER_ACCEPTED','DRIVER_EN_ROUTE','DRIVER_ARRIVED','PICKUP_VERIFIED','IN_PROGRESS','COMPLETING','COMPLETED','CANCELLED','EMERGENCY','DISPUTED'));

-- Production installations should add a trigger preventing UPDATE/DELETE on
-- mobility_events except through audited archival procedures.
