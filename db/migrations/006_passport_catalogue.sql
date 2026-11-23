-- Passport data-point catalogue (Commission guidance v3.2): typed synthetic evidence and guidance passages.
-- Applied once by /migrate.sh. Seed files: research/guidance/seed_evidence.py -> db/seed/passport_v3/.
BEGIN;

INSERT INTO source_records VALUES
 ('demo-inspection-v3', 'synthetic', '2026-11-23T00:00:00Z',
  'Fictional model-sheet entries for every public, industrial-mandatory placement data point of Commission guidance v3.2 (catalogue-v3.2-1). Supersedes demo-inspection-v1/v2 entries with the same chemistry. Planted gaps: BAT-DEMO-024, -031, -058, -077.')
ON CONFLICT DO NOTHING;

ALTER TABLE passport_fields ADD COLUMN IF NOT EXISTS unit text;
DELETE FROM passport_fields;

CREATE TEMP TABLE s_fields (battery_id text, field_code text, value_text text, unit text, evidence_ref text) ON COMMIT DROP;
\copy s_fields FROM '/seed/passport_v3/fields.csv' WITH (FORMAT csv, HEADER true, NULL '')
INSERT INTO passport_fields (battery_id, field_code, value_text, unit, evidence_ref, source_id)
SELECT battery_id, field_code, value_text, unit, evidence_ref, 'demo-inspection-v3' FROM s_fields;

CREATE TEMP TABLE s_passages (chunk_id text, title text, source_url text, section text, version text,
 access_class text, passage text, terms text) ON COMMIT DROP;
\copy s_passages FROM '/seed/passport_v3/passages.csv' WITH (FORMAT csv, HEADER true)
INSERT INTO document_chunks (chunk_id, title, source_url, section, version, access_class, passage, terms)
SELECT chunk_id, title, source_url, section, version, access_class, passage, terms FROM s_passages
ON CONFLICT (chunk_id) DO NOTHING;

INSERT INTO schema_migrations(version) VALUES ('006_passport_catalogue') ON CONFLICT DO NOTHING;
COMMIT;
