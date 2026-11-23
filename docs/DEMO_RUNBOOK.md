# Five-minute local investigation

Prerequisites: run the CALCE preparation and Docker startup commands in README. Use the default loopback ports, or substitute the configured web port. No LLM key is needed.

| Time | Action | Expected evidence |
| --- | --- | --- |
| 0:00–1:00 | From the workspace, open the fleet register. Set assessment date to 18 Feb 2027 and filter for missing evidence. Open BAT-DEMO-024. | One synthetic pack matches. Its identity is LFP with rated energy 16 kWh. |
| 1:00–2:00 | Inspect the field entries. Try 17 Feb 2027, then return to the preset. Review the bench records. | On the preset, chemistry has no supporting sheet reference, the rated capacity entry lacks a numeric Ah value, nominal voltage has evidence, the EV field is outside scope, and the recycled-content rule is future-effective. Simulated bench data is labeled. |
| 2:00–3:00 | Open the evidence assistant and submit “What is missing?”. Follow a citation. Try an unsupported approval request. | Offline mode shows two review findings and retrieved regulatory passages. An unsupported request returns the scope message. |
| 3:00–4:00 | Open cell research from the workspace. Select CS2_38 and expand the measurement references. | A measured discharge curve, timestamps, original workbook and cycle identifiers. The held-out linear MAE is about 0.0973 Ah. The research screen concerns experimental cells only. |
| 4:00–5:00 | Return to the 2027 pack inspector. Download the draft summary. | A dated Markdown draft includes gaps, synthetic provenance, rule versions, references, uncertainties and suggested expert checks. |

## Data dictionary

| Field or entity | Meaning |
| --- | --- |
| battery_id, vehicle_id | Fictional pack and truck identifiers. |
| rated_kwh / rated_ah / nominal_v | Rated energy in kWh, nominal charge capacity in Ah, and nominal voltage in V. They are separate fields. |
| source_type / source_id / observed_at | Evidence class, versioned origin and timestamp. Research tester timestamps have unspecified timezone. |
| as_of / effective_from | Prospective placement date used for assessment / earliest date modeled by that rule. |
| evidence_ref | Synthetic model-sheet reference. A missing reference identifies an evidence gap. |
| cell_id / cycle / source_cycle | CALCE experimental cell, retained discharge ordinal, and original within-workbook cycle index. |
| capacity_ah | Measured discharge-counter difference across a qualifying discharge step. |
| model_run_id | Identifies a fitted research artifact and pinned dataset. |
| chunk_id | Identifies the exact public passage returned by retrieval. |

Candidate value hypothesis: evidence-linked investigation may reduce preparation time for a specialist. Test this with timed investigations and expert review of missed evidence before making a savings claim.
