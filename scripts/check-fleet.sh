#!/bin/sh
# Integration check for an already running local Compose stack.
set -eu
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U passport <<'SQL'
DO $$
BEGIN
    IF (SELECT count(*) FROM batteries WHERE source_id = 'demo-identities-v2') <> 100
       OR (SELECT count(*) FROM batteries WHERE chemistry = 'LFP') <> 80
       OR EXISTS (SELECT FROM batteries WHERE (chemistry = 'lead-acid') <> (substr(battery_id, 10)::int % 5 = 0))
       OR (SELECT count(DISTINCT battery_id) FROM pack_daily) <> 100
       OR (SELECT max(day) FROM pack_daily) <> '2026-10-31'
       OR to_regclass('vehicle_assignments') IS NOT NULL
       OR (SELECT count(*) FROM fleet_seed_manifest) <> 1
       OR EXISTS (
           SELECT FROM generate_series(1, 100) AS seed(i)
           LEFT JOIN batteries b ON b.battery_id = 'BAT-DEMO-' || lpad(i::text, 3, '0')
           LEFT JOIN source_records s ON s.source_id = b.source_id
           WHERE b.rated_kwh IS DISTINCT FROM 16 + 4 * (i % 8)
              OR s.source_type IS DISTINCT FROM 'synthetic'
       ) THEN
        RAISE EXCEPTION 'Invalid synthetic fleet seed';
    END IF;
END $$;
SQL
docker compose exec -T api .venv/bin/python - <<'PY'
import json
from urllib.error import HTTPError
from urllib.request import urlopen

url = 'http://localhost:8000/api/batteries/'
with urlopen(url + 'BAT-DEMO-024', timeout=5) as response:
    battery = json.load(response)
assert battery == {
    'battery_id': 'BAT-DEMO-024', 'category': 'industrial', 'chemistry': 'LFP',
    'rated_kwh': 16, 'source_type': 'synthetic', 'source_id': 'demo-identities-v2',
    'observed_at': '2026-11-23T00:00:00Z',
    'explanation': 'Fictional identities v2: lead-acid when index divisible by 5, otherwise LFP; rated energy 16 + 4 × (index mod 8) kWh.'
}
try:
    urlopen(url + 'BAT-DEMO-101', timeout=5)
except HTTPError as exc:
    assert exc.code == 404
else:
    raise AssertionError('Unknown battery should return 404')
print('Fleet identity, provenance and unknown-ID checks passed')
PY
docker compose exec -T api .venv/bin/python - <<'PY'
import json
from urllib.request import urlopen
url = "http://localhost:8000/api/batteries"
def get(path):
    with urlopen(url + path, timeout=10) as response:
        return json.load(response)
data = get("/BAT-DEMO-024/passport-readiness?as_of=2027-02-18")
gaps = {r["rule_id"]: r["status"] for r in data["results"] if r["status"] in ("missing_evidence", "invalid")}
assert gaps == {"DP-12": "missing_evidence", "DP-11": "invalid"}, gaps
assert len(data["results"]) == 72 and {r["rule_id"]: r["status"] for r in data["results"]}["DP-25"] == "not_applicable"
assert data["health"]["battery_id"] == "BAT-DEMO-024"
assert get("?status=invalid&as_of=2027-02-18")["total"] == 2
assert get("?status=missing_evidence&as_of=2027-02-18")["total"] == 3
assert get("?query=BAT-DEMO-101")["total"] == 0
assert get("?page=9")["total"] == 100
print("Inspector, operational joins and fleet filters passed")
PY
