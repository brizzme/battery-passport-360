BEGIN;
CREATE TABLE IF NOT EXISTS source_records (
    source_id text PRIMARY KEY,
    source_type text NOT NULL CHECK (source_type IN ('synthetic','measured_public','derived','reference_document')),
    observed_at timestamptz NOT NULL,
    explanation text NOT NULL
);
CREATE TABLE IF NOT EXISTS batteries (
    battery_id text PRIMARY KEY,
    category text NOT NULL,
    chemistry text NOT NULL,
    rated_kwh integer NOT NULL CHECK (rated_kwh > 0),
    source_id text NOT NULL REFERENCES source_records
);
INSERT INTO source_records VALUES (
    'demo-identities-v1', 'synthetic', '2026-01-01T00:00:00Z',
    'Fictional seed snapshot. Chemistry and rated capacity are assigned by battery index.'
) ON CONFLICT DO NOTHING;
INSERT INTO batteries (battery_id, category, chemistry, rated_kwh, source_id)
SELECT 'BAT-DEMO-' || lpad(i::text, 3, '0'), 'industrial',
    CASE WHEN i % 2 = 0 THEN 'LFP' ELSE 'lead-acid' END,
    16 + 4 * (i % 8), 'demo-identities-v1'
FROM generate_series(1, 100) AS seed(i)
ON CONFLICT DO NOTHING;
INSERT INTO schema_migrations (version) VALUES ('002_demo_identities') ON CONFLICT DO NOTHING;
COMMIT;
