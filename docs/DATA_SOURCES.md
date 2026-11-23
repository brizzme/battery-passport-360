# Data sources

The service status comes from a live request to the local health endpoint. The underlying observation is a successful database query for the vector extension. Reloading the page requests a fresh observation.

## Source inventory

| Source | Intended use | Integration status |
| --- | --- | --- |
| [CALCE](https://calce.umd.edu/battery-data) and [MATR](https://data.matr.io/1/) | Experimental cell cycling measurements | CALCE integrated below; MATR candidate |
| [Regulation (EU) 2023/1542](https://eur-lex.europa.eu/eli/reg/2023/1542/ojn) | Source for illustrative readiness rules | Verified rule reference |
| [BatteryPass-Ready](https://thebatterypass.eu/battery-pass-ready/resources/) | Supporting guidance | Candidate reference |

The measured-data manifest below applies to CALCE only. MATR has not been ingested.

## Synthetic identity seed

Migration 002 generates BAT-DEMO-001 through BAT-DEMO-100 in order, using a fixed fictional snapshot date (2026-01-01 UTC) and source ID demo-identities-v1. Migration 005 moves them to demo-identities-v2 (2026-11-23): lead-acid when the index is divisible by 5, otherwise LFP (80 LFP, 20 lead-acid). The 50 chemistry model-sheet entries that changed are recorded under demo-inspection-v2; BAT-DEMO-024's entries are unchanged. Rated energy is 16 + 4 × (index modulo 8) kWh. All 100 identities reference the same versioned synthetic source. These values are assigned fixtures, with no measured cell or vehicle linkage.

## CALCE measured data (verified 2026-11-23)

Downloaded and parsed the four University of Maryland CALCE CS2 Type 2 archives (1C cycling). The source page permits open access and requests citation of the papers describing the experiments. No explicit raw redistribution license was identified there. Raw archives and extracted cycle records stay in ignored local downloads. Attribution: CALCE, University of Maryland; He, Williard, Osterman & Pecht, Journal of Power Sources 196 (2011), 10314–10321; Xing et al., Microelectronics Reliability 53 (2013), 811–820, as listed by [CALCE](https://calce.umd.edu/battery-data#CS2).

[Archive checksums](../research/calce.sha256) pin the bytes. The [run manifest](../apps/api/app/artifacts/calce-report.json) gives exact archive URLs, sizes, retained counts and date ranges. Parsed Excel Channel sheets using Cycle_Index, Step_Index, Date_Time, Voltage(V), Current(A), Discharge_Capacity(Ah). For cycles containing steps 6, 7 and 8, retained step 7 ending at 2.65–2.75 V and −1.15 to −1.05 A. Subtracted the last step-6 counter from the last step-7 counter. Duplicate timestamps with equal values across overlapping files count once. Timestamps are original tester clock times, timezone unspecified. The position on the chart counts retained discharges, starting at one. No rescaling from nominal pack capacities.

## Passport references and simulated bench data

Reviewed the [published EU regulation](https://eur-lex.europa.eu/eli/reg/2023/1542/oj/eng) on 2026-11-23. Rules v1.0 use Article 77(1) and Annex XIII 1(b,g,h,k,e) with Article 8(1). They assume prospective first placement on the assessment date. Article 8's conditional date remains unresolved at or after its earliest modeled date. Checks cover selected field components only. BatteryPass-Ready is supporting guidance. The M1 generator adds one fictional bench assignment, charge, BMS observation and service note per identity, with a shared versioned provenance record and fixed observation times.

## Reference index

Migration 004 embeds short public excerpts of the original 2023 OJ text of Regulation (EU) 2023/1542. Seven chunks carry publication version, exact article or annex point, public access class, and EUR-Lex URL. Typographic whitespace was normalized. The index is limited to the illustrative checks in this demo. Original EU legal documents are available for reuse with acknowledgement of their source; see [EUR-Lex legal notice](https://eur-lex.europa.eu/content/legal-notice/legal-notice.html?locale=en). No third-party technical manual or uploaded customer document is indexed.

## Calibrated synthetic fleet history (accessed 2026-11-23)

All pack history is **synthetic**. Selected parameters are derived from two public LFP datasets, both CC BY 4.0:

| Source ID | Dataset | Used for | Pinned files |
| --- | --- | --- | --- |
| hust-lfp-v2 | Ma, G. et al. (2022), Energy Environ. Sci.; [Mendeley Data 10.17632/nsc7hnsg4s.2](https://data.mendeley.com/datasets/nsc7hnsg4s/2). 77 LFP/graphite 1.1 Ah cells, 30 °C, 5C fast charge. | Cell-to-cell spread of cycles to 80 % (median 1,706, n = 77, none excluded) and the median fade-curve shape | our_data.zip, 1,188,136,932 bytes |
| aalborg-forklift-v2 | Vilsen, S. B. & Stroe, D.-I. (2024), Data in Brief; [Mendeley Data yz4pttm73n v2](https://data.mendeley.com/datasets/yz4pttm73n/2). Three 180 Ah prismatic LFP cells aged on a forklift profile at 45/40/35 °C. | Capacity fade per equivalent full cycle and its temperature dependence (Arrhenius fit), resistance growth per unit fade, duty-cycle shape | 160 RPT.csv and 3 Ageing.csv (Round10) |

Checksums come from the host API and are pinned in [research/calibration.sha256](../research/calibration.sha256). Raw files stay in ignored downloads/. Derived values and fit residuals are in [fleet-calibration.json](../apps/api/app/artifacts/fleet-calibration.json).

Transformations: Aalborg capacity is the Ah of the longest −45 A (C/4) discharge in each reference test, relative to Round00. Resistance is the voltage drop over the third 20 s, 45 A discharge pulse (50 % SOC) divided by 45 A. Equivalent full cycles per round come from one ageing round per cell. HUST discharge Ah per cycle is integrated from current inside the isolated extractor; life is the first cycle whose centred 5-cycle median falls below 80 % of the median of cycles 2–6.

Generator: [research/generate_fleet.py](../research/generate_fleet.py), version fleet-gen-v1, seed 20261123, daily rows 2024-11-01 to 2026-10-31. Hand-set assumptions (pack temperature rise per shift, event thresholds, state-of-charge model, opportunity charging, weekend activity) are listed in db/seed/fleet_v2/manifest.json and labelled `generator_assumption` in the API. Planted cases: BAT-DEMO-007 fast fader (hot dock, 3 shifts, 5th-percentile life), BAT-DEMO-013 fictional cooling fault in October 2026, BAT-DEMO-042 idle August–September 2026, BAT-DEMO-024 ordinary health with its passport evidence gaps.

## Passport health-field mapping

Health indicators are mapped to Annex XIII point 4 using the European Commission's [Guidance Document: Digital Batteries Passport – data points by category](https://single-market-economy.ec.europa.eu/document/download/cd1e5e6c-4a4a-4b99-995a-49eb6916187e_en), v3.2, 19 October 2026, CC BY 4.0, accessed 2026-11-23. The guidance states that it is non-binding. The mapping is marked provisional and restricted access (legitimate interest); Annex VII Part A state of health is reported as not applicable to these non-stationary packs.

## Passport data-point catalogue (accessed 2026-11-23)

The readiness rules come from the European Commission, *Guidance Document: Digital Batteries Passport – data points by category*, version 3.2, 19 October 2026, DG GROW, CC BY 4.0. The guidance states that it is non-binding and not an authoritative interpretation. The PDF (433,954 bytes, sha256 in [research/guidance.sha256](../research/guidance.sha256)) is downloaded to ignored `downloads/guidance/` and parsed by [research/guidance/parse.py](../research/guidance/parse.py) with pypdf into [passport-catalogue.json](../apps/api/app/artifacts/passport-catalogue.json): 71 data points, DP 38 split into cell (38a) and pack (38b) resistance, 72 rows. Ten rows that the PDF text layer splits across page breaks or footnotes are completed from [overrides.json](../research/guidance/overrides.json); each override carries its page and was checked against the PDF. Each row keeps the guidance cell text verbatim for EV, LMT and industrial batteries and a normalised applicability kind.

Migration 006 indexes one reference passage per row (`GUID-DP-*`), built from the row's name, legal reference, access class and verbatim applicability cells, and loads synthetic model-sheet evidence (`demo-inspection-v3`) for every public, industrial-mandatory placement data point of all 100 fictional packs (plus the lead symbol, DP 42, for lead-acid packs). Values are fictional; links point to the reserved example.org domain. Planted gaps: BAT-DEMO-024 (DP 12 without reference, DP 11 entry "unit absent", which is not a number), BAT-DEMO-031 (no declaration-of-conformity link), BAT-DEMO-058 (nominal voltage "fifty"), BAT-DEMO-077 (no extinguishing agent). Regenerate with `research/guidance/seed_evidence.py`.

## HUST early-cycle life model (accessed 2026-11-23)

The HUST archive (pinned in research/calibration.sha256) is re-extracted by the isolated container, which now also writes, per cell, the capacity remaining to the 2.0 V cut-off along the final constant-current discharge stage at cycles 10 and 100 (`downloads/hust_csv/qv/`, ignored). Per-cell discharge protocols come from Microsoft BatteryML `preprocess_HUST.py` (MIT), which cites the paper's supplementary information; its code labels the final stage 1C, but the measured data shows 2.2 A for every cell, and the data is used. `research/life_model.py` writes the committed derived artifacts `hust-life-report.json` (metrics, per-cell out-of-fold predictions) and `hust-curves.json` (per cell: capacity curve downsampled to ≤ 60 points and a coarse ΔQ(V) curve), redistributed under CC BY 4.0 with attribution. See docs/MODEL_CARD.md.
