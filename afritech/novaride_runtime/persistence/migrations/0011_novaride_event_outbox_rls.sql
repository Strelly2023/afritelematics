-- NovaRide mobility-event outbox tenant isolation.
--
-- mobility_event_outbox already has its canonical tenant policy.
-- This migration activates RLS so that policy becomes enforceable.
--
-- This is additive and intentionally does not modify:
--   mobility_events
--   novaride_resilience_outbox
--   existing EventFabric runtime composition

ALTER TABLE mobility_event_outbox
    ENABLE ROW LEVEL SECURITY;
