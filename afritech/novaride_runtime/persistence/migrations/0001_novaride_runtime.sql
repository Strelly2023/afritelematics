-- NovaRide Universal Mobility Super Platform Runtime v2026.2
-- PostgreSQL control-plane schema contract. Production deployments must apply
-- RLS and service-specific ownership before accepting traffic.

CREATE TABLE IF NOT EXISTS rider_profiles (
    rider_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS driver_profiles (
    driver_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    vehicle_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS driver_eligibility (
    eligibility_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    driver_id TEXT NOT NULL,
    eligible BOOLEAN NOT NULL,
    reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    vehicle_compliant BOOLEAN NOT NULL DEFAULT false,
    safety_hold BOOLEAN NOT NULL DEFAULT false,
    compliance_hold BOOLEAN NOT NULL DEFAULT false,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS driver_availability (
    driver_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    requested_state TEXT NOT NULL,
    authoritative_state TEXT NOT NULL,
    dispatchable BOOLEAN NOT NULL DEFAULT false,
    active_shift_id TEXT,
    vehicle_id TEXT,
    location_fresh BOOLEAN NOT NULL DEFAULT false,
    server_confirmed_at TIMESTAMPTZ,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS driver_shifts (
    shift_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    driver_id TEXT NOT NULL,
    state TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS driver_offers (
    offer_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    driver_id TEXT NOT NULL,
    trip_id TEXT NOT NULL,
    state TEXT NOT NULL,
    estimated_earnings JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS driver_bids (
    bid_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    driver_id TEXT NOT NULL,
    offer_id TEXT NOT NULL,
    amount JSONB NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fare_quotes (
    quote_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    service_type TEXT NOT NULL,
    currency TEXT NOT NULL,
    payload JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    rider_id TEXT NOT NULL,
    service_type TEXT NOT NULL,
    state TEXT NOT NULL,
    fare_quote_id TEXT,
    trip_id TEXT,
    pickup JSONB NOT NULL,
    destination JSONB NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    booking_id TEXT NOT NULL,
    rider_id TEXT NOT NULL,
    driver_id TEXT,
    vehicle_id TEXT,
    service_type TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    payment_reference TEXT,
    evidence_reference TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trip_locations (
    location_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    trip_id TEXT NOT NULL,
    point JSONB NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS operator_commands (
    command_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    command_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    authority_decision TEXT NOT NULL,
    evidence_reference TEXT,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    category TEXT NOT NULL,
    state TEXT NOT NULL,
    severity TEXT NOT NULL,
    owner_id TEXT,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS emergencies (
    emergency_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    trip_id TEXT,
    state TEXT NOT NULL,
    evidence_locked BOOLEAN NOT NULL DEFAULT true,
    visible_reference TEXT NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fleets (
    fleet_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fleet_drivers (
    fleet_driver_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    fleet_id TEXT NOT NULL,
    driver_id TEXT NOT NULL,
    status TEXT NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fleet_vehicles (
    fleet_vehicle_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    fleet_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    compliant BOOLEAN NOT NULL DEFAULT true,
    fuel_or_ev_state TEXT NOT NULL DEFAULT 'UNKNOWN',
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fleet_schedules (
    schedule_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    fleet_id TEXT NOT NULL,
    driver_id TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fleet_compliance (
    fleet_compliance_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    fleet_id TEXT NOT NULL,
    compliance_hold BOOLEAN NOT NULL DEFAULT false,
    reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS delivery_orders (
    order_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    pickup JSONB NOT NULL,
    dropoff JSONB NOT NULL,
    package_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    state TEXT NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS delivery_stops (
    stop_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    order_id TEXT NOT NULL,
    stop_type TEXT NOT NULL,
    address JSONB NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corporate_accounts (
    account_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    name TEXT NOT NULL,
    wallet_reference TEXT,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corporate_travel_policies (
    policy_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    account_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corporate_bookings (
    corporate_booking_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    account_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    booking_id TEXT NOT NULL,
    cost_center_id TEXT,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transit_routes (
    route_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    route_name TEXT NOT NULL,
    mode TEXT NOT NULL,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transit_stops (
    stop_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    name TEXT NOT NULL,
    point JSONB,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transit_journeys (
    journey_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    rider_id TEXT NOT NULL,
    legs JSONB NOT NULL,
    first_mile_booking_id TEXT,
    last_mile_booking_id TEXT,
    aggregate_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mobility_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_version BIGINT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    tenant_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    causation_id TEXT,
    schema_version TEXT NOT NULL,
    payload JSONB NOT NULL,
    integrity_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_replay_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    consumer_name TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    last_event_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS idempotency_records (
    tenant_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    command_hash TEXT NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS read_model_checkpoints (
    model_name TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    last_event_id TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (model_name, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_mobility_events_aggregate ON mobility_events (aggregate_id, aggregate_version);
CREATE INDEX IF NOT EXISTS idx_mobility_events_correlation ON mobility_events (correlation_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_bookings_tenant_region ON bookings (tenant_id, region_code, state);
CREATE INDEX IF NOT EXISTS idx_trips_tenant_region ON trips (tenant_id, region_code, lifecycle_state);
