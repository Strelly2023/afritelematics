-- NovaRide tenant-persistence isolation completion.
--
-- NCCS-05 / INVARIANT-TENANT-001
--
-- No operation executed under Tenant A may read, modify, delete,
-- emit, or otherwise expose authoritative state belonging to Tenant B.
--
-- Historical migrations remain immutable.
-- Canonical runtime tenant context:
--
--     app.tenant_id

DROP POLICY IF EXISTS novaride_corporate_accounts_tenant_isolation
    ON corporate_accounts;
CREATE POLICY novaride_corporate_accounts_tenant_isolation
    ON corporate_accounts
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_corporate_bookings_tenant_isolation
    ON corporate_bookings;
CREATE POLICY novaride_corporate_bookings_tenant_isolation
    ON corporate_bookings
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_corporate_travel_policies_tenant_isolation
    ON corporate_travel_policies;
CREATE POLICY novaride_corporate_travel_policies_tenant_isolation
    ON corporate_travel_policies
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_delivery_orders_tenant_isolation
    ON delivery_orders;
CREATE POLICY novaride_delivery_orders_tenant_isolation
    ON delivery_orders
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_delivery_stops_tenant_isolation
    ON delivery_stops;
CREATE POLICY novaride_delivery_stops_tenant_isolation
    ON delivery_stops
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_driver_availability_tenant_isolation
    ON driver_availability;
CREATE POLICY novaride_driver_availability_tenant_isolation
    ON driver_availability
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_driver_bids_tenant_isolation
    ON driver_bids;
CREATE POLICY novaride_driver_bids_tenant_isolation
    ON driver_bids
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_driver_eligibility_tenant_isolation
    ON driver_eligibility;
CREATE POLICY novaride_driver_eligibility_tenant_isolation
    ON driver_eligibility
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_driver_offers_tenant_isolation
    ON driver_offers;
CREATE POLICY novaride_driver_offers_tenant_isolation
    ON driver_offers
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_driver_profiles_tenant_isolation
    ON driver_profiles;
CREATE POLICY novaride_driver_profiles_tenant_isolation
    ON driver_profiles
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_driver_shifts_tenant_isolation
    ON driver_shifts;
CREATE POLICY novaride_driver_shifts_tenant_isolation
    ON driver_shifts
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_emergencies_tenant_isolation
    ON emergencies;
CREATE POLICY novaride_emergencies_tenant_isolation
    ON emergencies
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_event_replay_checkpoints_tenant_isolation
    ON event_replay_checkpoints;
CREATE POLICY novaride_event_replay_checkpoints_tenant_isolation
    ON event_replay_checkpoints
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_fleet_compliance_tenant_isolation
    ON fleet_compliance;
CREATE POLICY novaride_fleet_compliance_tenant_isolation
    ON fleet_compliance
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_fleet_drivers_tenant_isolation
    ON fleet_drivers;
CREATE POLICY novaride_fleet_drivers_tenant_isolation
    ON fleet_drivers
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_fleet_schedules_tenant_isolation
    ON fleet_schedules;
CREATE POLICY novaride_fleet_schedules_tenant_isolation
    ON fleet_schedules
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_fleet_vehicles_tenant_isolation
    ON fleet_vehicles;
CREATE POLICY novaride_fleet_vehicles_tenant_isolation
    ON fleet_vehicles
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_fleets_tenant_isolation
    ON fleets;
CREATE POLICY novaride_fleets_tenant_isolation
    ON fleets
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_incidents_tenant_isolation
    ON incidents;
CREATE POLICY novaride_incidents_tenant_isolation
    ON incidents
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_mobility_events_tenant_isolation
    ON mobility_events;
CREATE POLICY novaride_mobility_events_tenant_isolation
    ON mobility_events
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_operator_commands_tenant_isolation
    ON operator_commands;
CREATE POLICY novaride_operator_commands_tenant_isolation
    ON operator_commands
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_read_model_checkpoints_tenant_isolation
    ON read_model_checkpoints;
CREATE POLICY novaride_read_model_checkpoints_tenant_isolation
    ON read_model_checkpoints
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_transit_journeys_tenant_isolation
    ON transit_journeys;
CREATE POLICY novaride_transit_journeys_tenant_isolation
    ON transit_journeys
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_transit_routes_tenant_isolation
    ON transit_routes;
CREATE POLICY novaride_transit_routes_tenant_isolation
    ON transit_routes
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_transit_stops_tenant_isolation
    ON transit_stops;
CREATE POLICY novaride_transit_stops_tenant_isolation
    ON transit_stops
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_trip_locations_tenant_isolation
    ON trip_locations;
CREATE POLICY novaride_trip_locations_tenant_isolation
    ON trip_locations
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_trips_tenant_isolation
    ON trips;
CREATE POLICY novaride_trips_tenant_isolation
    ON trips
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

ALTER TABLE mobility_event_outbox
    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS novaride_mobility_event_outbox_tenant_isolation
    ON mobility_event_outbox;
CREATE POLICY novaride_mobility_event_outbox_tenant_isolation
    ON mobility_event_outbox
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

ALTER TABLE novaride_event_replay_plans
    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS novaride_event_replay_plans_tenant_isolation
    ON novaride_event_replay_plans;
CREATE POLICY novaride_event_replay_plans_tenant_isolation
    ON novaride_event_replay_plans
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_trip_ratings_tenant_isolation
    ON trip_ratings;
CREATE POLICY novaride_trip_ratings_tenant_isolation
    ON trip_ratings
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_support_cases_tenant_isolation
    ON support_cases;
CREATE POLICY novaride_support_cases_tenant_isolation
    ON support_cases
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );

DROP POLICY IF EXISTS novaride_operations_records_tenant_isolation
    ON novaride_operations_records;
CREATE POLICY novaride_operations_records_tenant_isolation
    ON novaride_operations_records
    USING (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    )
    WITH CHECK (
        tenant_id::text =
        NULLIF(current_setting('app.tenant_id', true), '')
    );
