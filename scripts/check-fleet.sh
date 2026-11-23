#!/bin/sh
# Integration check for an already running local Compose stack.
set -eu
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U passport <<'SQL'
DO $$
BEGIN
    IF (SELECT count(*) FROM batteries WHERE source_id = 'demo-identities-v1') <> 100
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
    'rated_kwh': 16, 'source_type': 'synthetic', 'source_id': 'demo-identities-v1',
    'observed_at': '2026-01-01T00:00:00Z',
    'explanation': 'Fictional seed snapshot. Chemistry and rated capacity are assigned by battery index.'
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
assert [r["status"] for r in data["results"]] == ["missing_evidence","invalid","present","not_applicable","not_yet_effective"]
assert data["bench"]["vehicle_id"] == "TRUCK-DEMO-024"
assert get("?status=invalid&as_of=2027-02-18")["total"] == 1
assert get("?query=BAT-DEMO-101")["total"] == 0
assert get("?page=9")["total"] == 100
print("Inspector, operational joins and fleet filters passed")
PY
