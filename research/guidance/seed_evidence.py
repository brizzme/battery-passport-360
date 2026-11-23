"""Generate deterministic synthetic model-sheet evidence and guidance passages for migration 006.

Run: (cd apps/api && uv run --locked --group research python ../../research/guidance/seed_evidence.py)
Evidence covers every public, industrial-mandatory, placement-time data point (plus DP 42 for lead-acid).
All values are fictional and labelled synthetic by their source record.
"""
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAT = json.loads((ROOT / "apps/api/app/artifacts/passport-catalogue.json").read_text())
OUT = ROOT / "db/seed/passport_v3"
IN_USE = ("Annex XIII 4 (a)", "Annex XIII 4 (c)", "Annex XIII 4 (d)")
PLANTED = {  # battery_id -> {field: "missing" | "missing_ref" | ("invalid", value, unit)}
    "BAT-DEMO-024": {"DP-12": "missing_ref", "DP-11": ("invalid", "unit absent", None)},
    "BAT-DEMO-031": {"DP-43": "missing"},
    "BAT-DEMO-058": {"DP-27": ("invalid", "fifty", "V")},
    "BAT-DEMO-077": {"DP-14": "missing"},
}


def targets() -> list[dict]:
    rows = []
    for r in CAT["rows"]:
        k = r["kind"]["industrial"]
        if r["access"] == "public" and r["legal_ref"] not in IN_USE and k in {"mandatory", "chemistry_conditional"}:
            rows.append(r)
    return rows


def pack(i: int) -> dict:
    lead = i % 5 == 0
    kwh = 16 + 4 * (i % 8)
    v = 48.0 if lead else 51.2
    return {"id": f"BAT-DEMO-{i:03d}", "lead": lead, "chem": "lead-acid" if lead else "LFP", "kwh": kwh, "v": v,
            "ah": round(kwh * 1000 / v), "month": f"{2023 + (i % 3)}-{(i % 12) + 1:02d}"}


def value(dp: str, p: dict) -> tuple[str, str | None] | None:
    lead, sheet = p["lead"], f"SHEET-{p['id']}"
    table = {
        "DP-1": (f"urn:demo:bp360:{p['id']}", None),
        "DP-2": ("Fictional Example Battery Co. (synthetic)", None),
        "DP-3": ("Fictional Example Battery Co. (synthetic)", None),
        "DP-4": ("Demo Street 1, 00000 Exampletown, Fictional Country (synthetic)", None),
        "DP-6": ("industrial", None),
        "DP-7": (f"TRX-{p['kwh']}-{'PB' if lead else 'LFP'} / SN-{p['id'][-3:]}", None),
        "DP-8": ("Exampletown, Example Region, Fictional Country", None),
        "DP-9": (p["month"], None),
        "DP-10": (str(p["kwh"] * (30 if lead else 12)), "kg"),
        "DP-11": (str(p["ah"]), "Ah"),
        "DP-12": (p["chem"], None),
        "DP-13": ("Lead; sulfuric acid electrolyte (synthetic entry)" if lead else
                  "Lithium hexafluorophosphate in organic carbonate electrolyte (synthetic entry)", None),
        "DP-14": (f"Recorded in fictional model sheet {sheet}, section 5 (synthetic entry)", None),
        "DP-15": ("Antimony" if lead else "Lithium; natural graphite; phosphate rock", None),
        "DP-24": ("2.0", "%"),
        "DP-26": ("42.0" if lead else "40.0", "V"),
        "DP-27": (str(p["v"]), "V"),
        "DP-28": ("57.6" if lead else "58.4", "V"),
        "DP-29": (str(p["kwh"] * 500), "W"),
        "DP-30": (str(p["kwh"] * 750), "W"),
        "DP-34": ("-20 °C … 50 °C (storage, reference test in fictional model sheet)", "°C"),
        "DP-38a": ("1.0" if lead else "0.6", "mΩ"),
        "DP-38b": ("25" if lead else "12", "mΩ"),
        "DP-41": ("Yes", None),
        "DP-42": ("Pb", None) if lead else None,
        "DP-43": (f"https://example.org/demo/doc/{p['id']}.pdf", None),
        "DP-44": (f"Take-back through a fictional dealer network; details in {sheet}, section 9 (synthetic entry)", None),
    }
    if dp not in table:
        raise SystemExit(f"No synthetic value generator for {dp}")
    return table[dp]


def evidence_rows() -> list[list]:
    out = []
    for i in range(1, 101):
        p = pack(i)
        plant = PLANTED.get(p["id"], {})
        for row in targets():
            got = value(row["id"], p)
            if got is None:
                continue
            text, unit = got
            ref = f"SHEET-{p['id']}"
            rule = plant.get(row["id"])
            if rule == "missing":
                continue
            if rule == "missing_ref":
                ref = ""
            elif isinstance(rule, tuple):
                _, text, unit = rule
            out.append([p["id"], row["id"], text, unit or "", ref])
    return out


def passage_rows() -> list[list]:
    out = []
    for r in CAT["rows"]:
        g = r["guidance"]
        unit = f" [{r['unit']}]" if r["unit"] else ""
        passage = (f"{r['name']}{unit}. Legal reference: Regulation (EU) 2023/1542, {r['legal_ref']}. "
                   f"Access: {r['access'].replace('_', ' ')}. EV: {g['ev']}. LMT: {g['lmt']}. Industrial: {g['industrial']}.")
        terms = f"{r['name']} {r['unit'] or ''} data point {r['dp']} {r['id']} {r['legal_ref']}"
        out.append([f"GUID-{r['id']}", CAT["source"]["title"] + " v3.2", CAT["source"]["url"],
                    f"Data point {r['dp']}{r['sub'] or ''} · {r['legal_ref']}", "Guidance v3.2, 19 Oct 2026", "public",
                    passage, terms])
    return out


def write(path: Path, header: list[str], rows: list[list]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    path.write_text(buf.getvalue())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "fields.csv", ["battery_id", "field_code", "value_text", "unit", "evidence_ref"], evidence_rows())
    write(OUT / "passages.csv", ["chunk_id", "title", "source_url", "section", "version", "access_class", "passage", "terms"],
          passage_rows())
    print(len(evidence_rows()), "evidence rows;", len(passage_rows()), "passages")


if __name__ == "__main__":
    main()
