DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'mobility_events_integrity_hash_not_empty'
          AND conrelid = 'mobility_events'::regclass
    ) THEN
        ALTER TABLE mobility_events
            ADD CONSTRAINT mobility_events_integrity_hash_not_empty
            CHECK (length(integrity_hash) > 10);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'idempotency_command_hash_not_empty'
          AND conrelid = 'idempotency_records'::regclass
    ) THEN
        ALTER TABLE idempotency_records
            ADD CONSTRAINT idempotency_command_hash_not_empty
            CHECK (length(command_hash) > 10);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_state_valid'
          AND conrelid = 'bookings'::regclass
    ) THEN
        ALTER TABLE bookings
            ADD CONSTRAINT bookings_state_valid
            CHECK (state IN ('DRAFT','QUOTED','CONFIRMED','SEARCHING','ASSIGNED','CANCELLED','EXPIRED','CONVERTED_TO_TRIP'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'trips_state_valid'
          AND conrelid = 'trips'::regclass
    ) THEN
        ALTER TABLE trips
            ADD CONSTRAINT trips_state_valid
            CHECK (lifecycle_state IN ('CREATED','MATCHING','ASSIGNED','DRIVER_ACCEPTED','DRIVER_EN_ROUTE','DRIVER_ARRIVED','PICKUP_VERIFIED','IN_PROGRESS','COMPLETING','COMPLETED','CANCELLED','EMERGENCY','DISPUTED'));
    END IF;
END
$$;

-- Production installations should add a trigger preventing UPDATE/DELETE on
-- mobility_events except through audited archival procedures.
