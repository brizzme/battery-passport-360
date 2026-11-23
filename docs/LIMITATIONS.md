# Scope and limitations

The foundation reports service availability at the time of a request. A successful check covers API connectivity, database access and presence of the vector extension. It supplies no evidence about a battery.

The project is an independent prototype with no commercial affiliation. It cannot certify passport compliance, determine operational safety, or approve lifecycle decisions. Legal and safety decisions require qualified specialists. The model evaluated one held-out CALCE cell under one protocol. The evidence assistant retrieves seven public regulatory excerpts and accepts a small set of inspection questions. Legal dates and access classes outside the explicitly documented subset require separate review.

The stack is intended for a single developer on localhost. Public hosting requires authentication, authorization, restricted access classes, HTTPS, rate limits, privacy review and appropriate logging.

## Calibrated synthetic fleet

- Every pack value is simulated. Calibration makes selected parameters traceable to measurements; it does not make the fleet measured or predictive of real packs.
- Fade per cycle and its temperature dependence rest on three Aalborg cells, one per temperature. Most simulated days fall below the measured 35–45 °C range: values between 20 and 35 °C are extrapolated and labelled, and below 20 °C the 20 °C rate is used.
- Cell measurements are applied to fictional packs without a validated cell-to-pack model. Calendar ageing is not modelled.
- Below 80 % capacity the measured HUST curve ends. The generator extends it linearly with a 60 % floor; packs at the floor are not distinguishable.
- Lead-acid packs have no calibration source, so their capacity and resistance indicators are reported as unknown. Power fade and expected lifetime are not modelled.
- Review flags use demo thresholds. They are not safety, warranty or end-of-life limits, and the passport mapping is provisional until the rules are refreshed.
