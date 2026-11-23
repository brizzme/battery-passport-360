"""Parse Commission guidance 'Digital Batteries Passport - data points by category' v3.2 into a catalogue.

Run: (cd apps/api && uv run --locked --group research python ../../research/guidance/parse.py)
Rows the text layer splits across page breaks are completed from overrides.json (hand-checked against the PDF).
"""
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "downloads/guidance/dbp-v3.2.pdf"
PIN = ROOT / "research/guidance.sha256"
OUT = ROOT / "apps/api/app/artifacts/passport-catalogue.json"
OVERRIDES = Path(__file__).parent / "overrides.json"
URL = ("https://single-market-economy.ec.europa.eu/document/download/cd1e5e6c-4a4a-4b99-995a-49eb6916187e_en"
       "?filename=Digital%20Batteries%20Passport%20-%20data%20point%20by%20category.pdf")
HEADER = ("Item Data point name (clarifications stated in square brackets []) As defined in Data point source "
          "Type of information Electric vehicles (EV) Light means of transport (LMT) Industrial")
CELL_START = r"(?=\b(?:Mandatory|Not to be filled|Only |If applicable|Optional|Applicable as soon|Same as data point|Cadmium or lead)\b)"
ACCESS = re.compile(r"\b(Public|Restricted: Only to (?:persons with legitimate interests?(?: \(individual battery\))?"
                    r"(?:, notified bodies, MS authorities and COM)?|notified bodies, MS authorities and COM))")
REF = re.compile(r"BR (Annex [IVX]+(?: [A-Z0-9]+)?(?: \([a-z0-9]+\))?|Article \d+ \(\d+\))")
N_ROWS = 71


def classify(cell: str) -> str:
    c = cell.strip()
    if c.startswith("Same as data point") or "repetition" in c:
        return "not_filled_repetition"
    if c.startswith("Not to be filled") and ("as of February 2027" in c or "required from" in c or "on hold" in c):
        return "not_filled_until_act"
    if c.startswith("Not to be filled"):
        return "not_filled"
    if c.startswith("Only applicable for some industrial"):
        return "some_industrial"
    if c.startswith("Only for rechargeable"):
        return "rechargeable_only"
    if c.startswith("Only for stationary"):
        return "stationary_only"
    if c.startswith("Cadmium or lead"):
        return "chemistry_conditional"
    if c.startswith("If applicable"):
        return "if_applicable"
    if c.startswith("Optional"):
        return "optional"
    if c.startswith("Applicable as soon"):
        return "in_use"
    if c.startswith("Mandatory"):
        return "mandatory"
    return "unparsed"


def split_cells(text: str) -> list[str]:
    return [p.strip() for p in re.split(CELL_START, text) if p.strip()]


def value_type(bracket: str) -> str:
    b = bracket.lower()
    if "web link" in b:
        return "link"
    if "yes/no" in b:
        return "yes_no"
    if "month" in b and "year" in b:
        return "month_year"
    if "code list" in b:
        return "code_list"
    if "free text" in b:
        return "free_text"
    if b.startswith("unit") or b in {"%", "number", "in number", "months", "years"} or "unit " in b:
        return "number"
    return "free_text"


def unit_of(bracket: str) -> str | None:
    if bracket.strip() == "%":
        return "%"
    b = bracket.strip()
    m = re.match(r"unit ([^,\]]+)", b)
    if m:
        return m.group(1).strip()
    if b in {"months", "years"}:
        return b
    return "°C" if "°C" in b else None


def rows_from_text(text: str) -> list[dict]:
    flat = re.sub(r"\s+", " ", text)
    flat = re.sub(r" \d{1,2} " + re.escape(HEADER), " ", flat)
    flat = flat.replace(HEADER, " ")
    pos = flat.index("1. Unique identifier")
    starts = []
    for n in range(1, N_ROWS + 1):
        i = flat.index(f"{n}. ", pos)
        starts.append(i)
        pos = i + 1
    rows = []
    for n, (a, b) in enumerate(zip(starts, starts[1:] + [len(flat)]), 1):
        raw = flat[a + len(f"{n}. "):b].strip()
        rows.append(parse_row(n, raw))
    return rows


def parse_row(n: int, raw: str) -> dict:
    m = re.search(r" \[|\bN/A\b| BR ", raw)
    name = raw[:m.start()].strip() if m else raw
    bracket = ""
    rest = raw[m.start():] if m else ""
    if rest.startswith(" ["):
        close = rest.index("]")
        bracket, rest = rest[2:close], re.sub(r"^\d+", "", rest[close + 1:])
    acc = ACCESS.search(rest)
    refs = REF.findall(rest[:acc.start()] if acc else rest)
    cells = split_cells(rest[acc.end():]) if acc else []
    access = None if not acc else ("public" if acc.group(1) == "Public" else
                                   "restricted_authorities" if "persons" not in acc.group(1) else
                                   "restricted_legitimate_interest")
    return {"dp": n, "name": name, "bracket": bracket, "legal_ref": refs[-1] if refs else None,
            "access": access, "cells": cells[:3], "raw": raw}


def build(rows: list[dict], overrides: dict, sha: str) -> dict:
    out, problems = [], []
    for r in rows:
        o = overrides.get(str(r["dp"]), {})
        r = {**r, **{k: v for k, v in o.items() if k not in {"note", "split"}}}
        if len(r["cells"]) != 3 or not r["legal_ref"] or not r["access"]:
            problems.append(r["dp"])
            continue
        kinds = dict(zip(("ev", "lmt", "industrial"), (classify(c) for c in r["cells"])))
        if "unparsed" in kinds.values():
            problems.append(r["dp"])
            continue
        base = {"dp": r["dp"], "sub": None, "name": r["name"], "unit": o.get("unit", unit_of(r["bracket"])),
                "value_type": o.get("value_type", value_type(r["bracket"])), "legal_ref": r["legal_ref"],
                "access": r["access"], "guidance": dict(zip(("ev", "lmt", "industrial"), r["cells"])), "kind": kinds}
        if "split" in o:
            for sub, name in o["split"].items():
                out.append({**base, "id": f"DP-{r['dp']}{sub}", "sub": sub, "name": name})
        else:
            out.append({**base, "id": f"DP-{r['dp']}"})
    if problems:
        raise SystemExit(f"Rows need overrides (check them in the PDF): {problems}")
    return {"version": "catalogue-v3.2-1",
            "source": {"title": "Guidance Document: Digital Batteries Passport - data points by category",
                       "version": "3.2", "date": "2026-10-19", "url": URL, "sha256": sha, "accessed": "2026-11-23",
                       "licence": "CC BY 4.0", "publisher": "European Commission, DG GROW",
                       "status": "non-binding guidance; not an authoritative interpretation"},
            "rows": out}


def main():
    expected = PIN.read_text().split()[0]
    if not PDF.exists():
        PDF.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (research-client)"})
        PDF.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    sha = hashlib.sha256(PDF.read_bytes()).hexdigest()
    if sha != expected:
        raise SystemExit("Guidance PDF checksum mismatch")
    from pypdf import PdfReader
    text = "\n".join(p.extract_text() for p in PdfReader(PDF).pages)
    rows = rows_from_text(text)
    if "--dump" in sys.argv:
        for r in rows:
            print(r["dp"], "|", r["name"], "|", r["bracket"], "|", r["legal_ref"], "|", r["access"], "|", r["cells"])
        return
    catalogue = build(rows, json.loads(OVERRIDES.read_text()), sha)
    OUT.write_text(json.dumps(catalogue, indent=1, ensure_ascii=False) + "\n")
    print(len(catalogue["rows"]), "rows")


if __name__ == "__main__":
    main()
