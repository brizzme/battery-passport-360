#!/bin/sh
# Read-only API integration checks against the local Compose project.
set -eu
./scripts/check-fleet.sh
docker compose exec -T api .venv/bin/python - <<'PY'
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = "http://localhost:8000/api"
def post(path, data):
    return urlopen(Request(base+path, data=json.dumps(data).encode(), headers={"Content-Type":"application/json"}), timeout=15)
def get(path):
    return json.load(urlopen(base+path, timeout=5))

ref = {p["chunk_id"]:p for p in get("/reference-sources")}
sample = {"battery_id":"BAT-DEMO-024","as_of":"2027-02-18"}
answer = json.load(post("/copilot/query",{**sample,"question":"What is missing?"}))
assert answer["supported"] and {f["field"] for f in answer["findings"]} == {"DP-11","DP-12"}
assert all(ref[p["chunk_id"]]==p for p in answer["passages"])
cited = {p["chunk_id"] for p in answer["passages"]}
assert all(set(f["citation_ids"]) <= cited for f in answer["findings"])
assert not json.load(post("/copilot/query",{**sample,"question":"Approve resale"}))["supported"]
try:
    post("/copilot/query",{**sample,"battery_id":"BAT-DEMO-101","question":"What is missing?"})
except HTTPError as exc:
    assert exc.code == 404
else:
    raise AssertionError("Unknown battery should return 404")
with post("/inspection-summaries",sample) as response:
    assert "attachment" in response.headers["Content-Disposition"]
    body = response.read().decode()
    assert all(s in body for s in ("Draft investigation","Synthetic","missing_evidence","DP-11","DP-12","Guidance v3.2","Annex VI A (6)","2027-02-18","Expert review","HUST","Aalborg"))
report = get("/research/model-report")
assert report["status"] == "trained" and set(report["train_cells"]).isdisjoint(report["test_cells"])
for cell in get("/research/cells"):
    if cell["cycles_available"]:
        series=get("/research/cells/"+cell["cell_id"]+"/cycles")
        assert len(series["points"])==report["sources"][cell["cell_id"]]["cycles"]
fleet = get("/fleet/health-summary")
assert fleet["packs"] == 100 and fleet["data_cutoff"] == "2026-10-31" and fleet["source_type"] == "synthetic"
flagged = {f["battery_id"] for f in fleet["review"]}
assert {"BAT-DEMO-024", "BAT-DEMO-007", "BAT-DEMO-013"} <= flagged, flagged
assert len(fleet["pack_points"]) == 100 and abs(sum(fleet["regime_share"].values()) - 1) < 1e-6
lead = {i["key"]: i for i in get("/batteries/BAT-DEMO-005/health-summary")["indicators"]}
assert lead["capacity_fade_pct"]["status"] == "unknown"
h = get("/batteries/BAT-DEMO-024/health-summary?as_of=2027-02-18")
assert h["data_cutoff"] == "2026-10-31" and h["as_of"] == "2026-10-31"
assert len(get("/batteries/BAT-DEMO-024/history")["points"]) == 365
print("Retrieved references, abstention, export, research report and fleet health verified.")
PY
