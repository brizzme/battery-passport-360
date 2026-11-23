BEGIN;
INSERT INTO source_records VALUES
 ('demo-inspection-v1','synthetic','2026-01-02T12:00:00Z','Deterministic fictional pre-market test-bench and model-sheet fixtures.')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS passport_fields (
 battery_id text REFERENCES batteries, field_code text, value_text text NOT NULL,
 evidence_ref text, source_id text NOT NULL REFERENCES source_records,
 PRIMARY KEY (battery_id, field_code)
);
CREATE TABLE IF NOT EXISTS vehicle_assignments (
 battery_id text PRIMARY KEY REFERENCES batteries, vehicle_id text UNIQUE NOT NULL,
 assigned_on date NOT NULL, source_id text NOT NULL REFERENCES source_records
);
CREATE TABLE IF NOT EXISTS charge_sessions (
 battery_id text REFERENCES batteries, started_at timestamptz, ended_at timestamptz NOT NULL,
 energy_kwh numeric NOT NULL CHECK (energy_kwh > 0), source_id text NOT NULL REFERENCES source_records,
 PRIMARY KEY (battery_id, started_at), CHECK (ended_at > started_at)
);
CREATE TABLE IF NOT EXISTS telemetry_samples (
 battery_id text REFERENCES batteries, observed_at timestamptz, soc_pct integer NOT NULL CHECK (soc_pct BETWEEN 0 AND 100),
 temperature_c integer NOT NULL, source_id text NOT NULL REFERENCES source_records, PRIMARY KEY (battery_id, observed_at)
);
CREATE TABLE IF NOT EXISTS service_events (
 battery_id text REFERENCES batteries, observed_at timestamptz, note text NOT NULL,
 source_id text NOT NULL REFERENCES source_records, PRIMARY KEY (battery_id, observed_at)
);

INSERT INTO passport_fields
SELECT battery_id, code, val,
 CASE WHEN battery_id='BAT-DEMO-024' AND code='chemistry' THEN NULL ELSE 'SHEET-' || battery_id END,
 'demo-inspection-v1'
FROM batteries CROSS JOIN LATERAL (VALUES
 ('chemistry', chemistry),
 ('rated_ah', CASE WHEN battery_id='BAT-DEMO-024' THEN 'unit absent' ELSE (rated_kwh * 20)::text END),
 ('nominal_v','50')
) fields(code,val) WHERE source_id='demo-identities-v1' ON CONFLICT DO NOTHING;
INSERT INTO vehicle_assignments
SELECT battery_id, replace(battery_id,'BAT','TRUCK'), '2026-01-01', 'demo-inspection-v1'
FROM batteries WHERE source_id='demo-identities-v1' ON CONFLICT DO NOTHING;
INSERT INTO charge_sessions
SELECT battery_id,'2026-01-02T06:00Z','2026-01-02T08:00Z',rated_kwh * 0.4,'demo-inspection-v1'
FROM batteries WHERE source_id='demo-identities-v1' ON CONFLICT DO NOTHING;
INSERT INTO telemetry_samples
SELECT battery_id,'2026-01-02T08:00Z',80,22,'demo-inspection-v1'
FROM batteries WHERE source_id='demo-identities-v1' ON CONFLICT DO NOTHING;
INSERT INTO service_events
SELECT battery_id,'2026-01-02T09:00Z','Recorded demo bench inspection','demo-inspection-v1'
FROM batteries WHERE source_id='demo-identities-v1' ON CONFLICT DO NOTHING;
INSERT INTO schema_migrations(version) VALUES ('003_inspector') ON CONFLICT DO NOTHING;
COMMIT;
