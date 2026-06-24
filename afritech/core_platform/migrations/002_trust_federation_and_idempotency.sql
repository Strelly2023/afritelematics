ALTER TABLE novatech_core_trust_packets
    ADD COLUMN IF NOT EXISTS intent_id TEXT,
    ADD COLUMN IF NOT EXISTS signature JSONB,
    ADD COLUMN IF NOT EXISTS source_node TEXT NOT NULL DEFAULT 'novatech-primary',
    ADD COLUMN IF NOT EXISTS imported BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS envelope_id TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS idx_novatech_core_trust_intent
ON novatech_core_trust_packets(organization_id, intent_id)
WHERE intent_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_novatech_core_trust_envelope
ON novatech_core_trust_packets(envelope_id)
WHERE envelope_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS novatech_payment_webhook_events (
    event_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    payment_id TEXT,
    provider_reference TEXT,
    settlement_status TEXT NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (provider, event_id)
);
