# Five-minute local walkthrough

Prerequisites: `docker compose up --build -d` (README). Everything below works from a fresh clone without downloads, accounts or an LLM key. All fleet data is fictional and labelled synthetic; research data is measured public data.

| Time | Action | Expected evidence |
| --- | --- | --- |
| 0:00–1:00 | Open [Fleet health](http://127.0.0.1:3000/fleet-health) (the home page is the PoC summary). Read the headline figures, the review table and the fleet floor. Hover a hatched tile at the hot dock. | 100 packs, 14 suggested for specialist review with reasons (11 on health signals, plus the passport-gap packs), wear concentrated at the hot dock. Hatch marks extrapolated or unknown values; BAT-DEMO-007 reads "≤ 60.0 % (model floor)". Every figure is labelled simulated and calibrated on public LFP data. |
| 1:00–2:00 | Scroll to the scatter, the temperature-model strip and "Where these numbers come from". | Capacity against cumulative cycles for LFP packs; most pack-days lie outside the measured 35–45 °C range and are labelled extrapolated or clamped; HUST and Aalborg sources with licences. |
| 2:00–3:00 | Open BAT-DEMO-024 from the review table (assessment 18 Feb 2027). Read the health charts, then the passport coverage strip and the open "Gaps" group. | 72 guidance data points: 2 gaps (DP 11 capacity entry not a number; DP 12 chemistry without a model-sheet reference), plus present, unresolved, not-yet-effective and not-applicable groups, each row citing the guidance data point and the regulation. |
| 3:00–4:00 | Click "Ask the evidence assistant", submit "What is missing?", follow a citation; then try "Approve resale". | Offline mode lists the two gaps citing GUID-DP-11, GUID-DP-12 and Article 77; 11 unresolved rows are reported as not gaps. The approval request returns the scope message. |
| 4:00–5:00 | Open [Cell research](http://127.0.0.1:3000/research). Compare the models, then click a point in the scatter. Finally download the draft summary from the pack page. | 77 measured HUST cells, leave-one-batch-out: training-mean baseline MAE 272 cycles, capacity features about 200; the voltage feature adds nothing (reported as a null result). The selected cell shows its capacity curve, life marker and ΔQ(V) curve. The Markdown draft lists coverage counts, every gap with references, and synthetic provenance. |

## Data dictionary

| Field or entity | Meaning |
| --- | --- |
| battery_id | Fictional pack identifier (BAT-DEMO-001…100). |
| rule_id (DP-n) | Data point n of the Commission guidance v3.2 catalogue; DP-38a/38b are cell and pack resistance. |
| status | present, missing_evidence, invalid, not_applicable, not_yet_effective, unknown. Gaps are missing_evidence or invalid only. |
| source_type / source_id / observed_at | Evidence class (synthetic, measured_public, derived, reference_document), versioned origin and timestamp. |
| as_of / effective_from / data_cutoff | Assessment date (prospective first placement) / earliest date a data point applies / last day of synthetic history (2026-10-31). |
| capacity_pct, temp_regime | Synthetic pack capacity in % of initial; whether the day's temperature lay in the calibrated, extrapolated or clamped range. |
| cell id (b-n), life | HUST laboratory cell in test batch b; cycles to 80 % of its initial capacity. |
| chunk_id | Exact passage returned by retrieval (EU-* regulation excerpts, GUID-DP-* guidance rows). |

Candidate value hypothesis: evidence-linked investigation may reduce preparation time for a specialist. Test it with timed investigations and expert review of missed evidence before making any savings claim.
