-- NovaRide trip rating persistence authority.
--
-- Rating binds to the authoritative trip. Rider and driver identities
-- remain authoritative properties of the trip and are not duplicated
-- into this table.
--
-- Transaction authority remains with NovaRide PostgreSQL UoW.

CREATE TABLE IF NOT EXISTS trip_ratings (
    rating_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL DEFAULT 1,
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    trip_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    comment TEXT NULL,

    CONSTRAINT trip_ratings_score_range
        CHECK (score >= 1 AND score <= 5),

    CONSTRAINT trip_ratings_one_per_trip
        UNIQUE (tenant_id, trip_id)
);

CREATE INDEX IF NOT EXISTS idx_trip_ratings_tenant
    ON trip_ratings (tenant_id);

CREATE INDEX IF NOT EXISTS idx_trip_ratings_trip
    ON trip_ratings (trip_id);

ALTER TABLE trip_ratings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS novaride_trip_ratings_tenant_isolation
    ON trip_ratings;

CREATE POLICY novaride_trip_ratings_tenant_isolation
    ON trip_ratings
    USING (
        tenant_id = NULLIF(
            current_setting(
                'app.current_tenant_id',
                true
            ),
            ''
        )
    )
    WITH CHECK (
        tenant_id = NULLIF(
            current_setting(
                'app.current_tenant_id',
                true
            ),
            ''
        )
    );
