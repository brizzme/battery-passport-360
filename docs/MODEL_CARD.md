# CALCE discharge-capacity baseline

Run calce-index-ols-v1-3b0d3ac7e4ba estimates laboratory cell discharge capacity (Ah) from one feature, the ordinal of the retained discharge for that cell. Use this to explore a measured trend. It supplies no pack-level remaining-life or service decision.

| Evaluation on CS2_38, 1,025 discharges | MAE (Ah) | RMSE (Ah) |
| --- | ---: | ---: |
| Training mean | 0.16252 | 0.20039 |
| Ordinary least squares | 0.09726 | 0.11337 |

Training used CS2_35, CS2_36 and CS2_37 (2,886 observations). The held-out cell supplied no training or tuning inputs. The fitted equation is 1.21090 − 0.000758391 × ordinal, in Ah. The constant baseline is the training mean of 0.844126 Ah. This exploratory estimate uses data from only one test cell and one nominal 1C protocol. No batch-independent validation or uncertainty calibration was performed. The index omits unretained cycles. Extrapolation beyond this range is unsupported.

Reproduce with the locked research preparation command in README. The persisted report stores coefficients, sample counts, full-precision metrics, training timestamp, archive digests and source URLs in apps/api/app/artifacts/calce-report.json.
