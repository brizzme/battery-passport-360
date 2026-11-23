-- Review fixes to demo-inspection-v3 evidence (seed already corrected for fresh databases; this updates applied ones).
BEGIN;
UPDATE passport_fields f SET value_text = 'Sulfuric acid electrolyte (synthetic entry)'
FROM batteries b WHERE f.battery_id = b.battery_id AND b.chemistry = 'lead-acid' AND f.field_code = 'DP-13'
  AND f.value_text <> 'Sulfuric acid electrolyte (synthetic entry)';
UPDATE passport_fields SET unit = NULL WHERE field_code = 'DP-34' AND unit IS NOT NULL;
INSERT INTO schema_migrations(version) VALUES ('007_catalogue_seed_fixes') ON CONFLICT DO NOTHING;
COMMIT;
