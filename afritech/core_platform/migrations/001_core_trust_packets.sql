CREATE TABLE IF NOT EXISTS novatech_core_trust_packets (
    id TEXT PRIMARY KEY,
    receipt_id TEXT,
    organization_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    packet JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_novatech_core_trust_receipt
ON novatech_core_trust_packets(receipt_id);

CREATE INDEX IF NOT EXISTS idx_novatech_core_trust_org
ON novatech_core_trust_packets(organization_id);
