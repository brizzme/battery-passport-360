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

Migration 002 generates BAT-DEMO-001 through BAT-DEMO-100 in order, using a fixed fictional snapshot date (2026-01-01 UTC) and source ID demo-identities-v1. Even indices receive LFP chemistry, odd indices lead-acid. Rated energy is 16 + 4 × (index modulo 8) kWh. All 100 identities reference the same versioned synthetic source. These values are assigned fixtures, with no measured cell or vehicle linkage.

## CALCE measured data (verified 2026-11-23)

Downloaded and parsed the four University of Maryland CALCE CS2 Type 2 archives (1C cycling). The source page permits open access and requests citation of the papers describing the experiments. No explicit raw redistribution license was identified there. Raw archives and extracted cycle records stay in ignored local downloads. Attribution: CALCE, University of Maryland; He, Williard, Osterman & Pecht, Journal of Power Sources 196 (2011), 10314–10321; Xing et al., Microelectronics Reliability 53 (2013), 811–820, as listed by [CALCE](https://calce.umd.edu/battery-data#CS2).

[Archive checksums](../research/calce.sha256) pin the bytes. The [run manifest](../apps/api/app/artifacts/calce-report.json) gives exact archive URLs, sizes, retained counts and date ranges. Parsed Excel Channel sheets using Cycle_Index, Step_Index, Date_Time, Voltage(V), Current(A), Discharge_Capacity(Ah). For cycles containing steps 6, 7 and 8, retained step 7 ending at 2.65–2.75 V and −1.15 to −1.05 A. Subtracted the last step-6 counter from the last step-7 counter. Duplicate timestamps with equal values across overlapping files count once. Timestamps are original tester clock times, timezone unspecified. The position on the chart counts retained discharges, starting at one. No rescaling from nominal pack capacities.

## Passport references and simulated bench data

Reviewed the [published EU regulation](https://eur-lex.europa.eu/eli/reg/2023/1542/oj/eng) on 2026-11-23. Rules v1.0 use Article 77(1) and Annex XIII 1(b,g,h,k,e) with Article 8(1). They assume prospective first placement on the assessment date. Article 8's conditional date remains unresolved at or after its earliest modeled date. Checks cover selected field components only. BatteryPass-Ready is supporting guidance. The M1 generator adds one fictional bench assignment, charge, BMS observation and service note per identity, with a shared versioned provenance record and fixed observation times.

## Reference index

Migration 004 embeds short public excerpts of the original 2023 OJ text of Regulation (EU) 2023/1542. Seven chunks carry publication version, exact article or annex point, public access class, and EUR-Lex URL. Typographic whitespace was normalized. The index is limited to the illustrative checks in this demo. Original EU legal documents are available for reuse with acknowledgement of their source; see [EUR-Lex legal notice](https://eur-lex.europa.eu/content/legal-notice/legal-notice.html?locale=en). No third-party technical manual or uploaded customer document is indexed.
