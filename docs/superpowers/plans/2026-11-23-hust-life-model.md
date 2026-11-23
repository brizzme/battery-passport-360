# HUST Early-Cycle Life Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Predict HUST LFP cell life (cycles to 80 % of initial capacity) from cycles ≤ 100 with leave-one-batch-out evaluation, conformal intervals and a rebuilt research page.

**Architecture:** Isolated extractor additionally writes remaining-capacity-vs-voltage curves for cycles 10 and 100 (final 1C stage). `research/lifemodel/` computes features and runs nested grouped evaluation (scikit-learn, research group). Committed artifacts feed new research API endpoints and the `/research` page.

**Tech Stack:** Python 3.12, numpy, scikit-learn (pinned via uv.lock, research group), pandas only inside the isolated container, FastAPI, Next.js.

**Spec:** [docs/superpowers/specs/2026-11-23-hust-life-model-design.md](../specs/2026-11-23-hust-life-model-design.md) — its calls are binding.

## Global Constraints
- Life = first cycle whose centred 5-cycle median < 0.8 × median(cycles 2–6) (`fleetcal.hust.life_to_80`).
- Features read cycles ≤ 100 only. Outer split: leave-one-batch-out (batch = id prefix 1…10). Inner model selection: GroupKFold by batch on training cells only.
- 80 % split-conformal intervals in log10 space from inner out-of-fold residuals; report empirical outer coverage.
- No external numeric yardsticks; baseline = training mean under the same split.
- Labels: "measured laboratory cells (HUST, CC BY 4.0)"; predictions `derived`; never fleet packs. Ink-only scatter marks.
- Untrusted pickles only in `docker run --network none --read-only --user nobody`.
- Commits per task with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; branch `feat/hust-life-model`.

## Review Focus
1. A cell whose final 1C segment starts below the grid maximum → grid trimmed to common coverage; no NaN in features. (Task 2)
2. Cell 7-5 (first cycles problematic per BatteryML) → cycles 10/100 still valid; life unaffected. (Task 2)
3. Elastic net selecting all-zero coefficients → model reduces to intercept; reported, not crashed. (Task 3)
4. Fresh clone without downloads → research page renders from committed artifacts. (Task 5)
5. Unknown cell id on the API → 404. (Task 4)

---

### Task 1: Extract Q(V) curves in the isolated container
**Files:** `research/hust_extract/extract.py` (keep CSV output byte-identical), `research/fleetcal/hust.py` (+ `read_qv(path) -> dict`), `research/tests/test_hust_qv.py`.
- Container writes `/out/qv/<cell>.json`: `{grid: [2.00..3.40 step 0.005], q10: [...], q100: [...], seg10: {start_v, start_cycle_time}, seg100: {...}}` where q = capacity remaining to the 2.0 V cut-off within the final contiguous ≈1C (|I+1100 mA| < 110 mA) discharge segment, NaN above the segment's start voltage; monotone enforced before interpolation.
- [ ] Test `read_qv` on a tiny fixture JSON; rebuild image; re-run extraction; confirm 77 qv files and CSVs unchanged (sha256 before/after); commit.

### Task 2: Features
**Files:** `research/lifemodel/__init__.py`, `research/lifemodel/features.py`, `research/tests/test_life_features.py`.
- `common_grid(qvs) -> np.ndarray` (grid points finite for every cell), `delta_q(qv, grid) -> np.ndarray`, `voltage_features(dq) -> {log_var, log_abs_min, mean}`, `capacity_features(cycles, cap) -> {q2, max_minus_q2, slope_91_100, intercept_91_100}` (raises if any cycle > 100 is read — implement by slicing to ≤100 first), `feature_table(cells) -> (ids, batches, X_voltage, X_capacity, y_life)`.
- [ ] Tests first (linear fixture recovers slope; ΔQ of identical curves → var 0 handled via floor 1e-12; features unchanged when cycles > 100 are altered); FAIL → implement → PASS; commit.

### Task 3: Evaluation
**Files:** `research/lifemodel/evaluate.py`, `research/tests/test_life_evaluate.py`; `apps/api/pyproject.toml` (+ scikit-learn, research group).
- `evaluate(X, y_log, batches, model) -> {pred_log, lo_log, hi_log, fold_metrics}` with outer LeaveOneGroupOut, inner GroupKFold(5) ElasticNetCV(l1_ratio [.1,.5,.9,1], standardised), baseline = mean; `metrics(y, pred)` in cycles.
- [ ] Tests first (no batch overlap per fold — assert via a spy; baseline equals per-fold training mean; coverage computed correctly; all-zero coefficients path works); FAIL → implement → PASS; commit.

### Task 4: Run, artifacts, verify, API
**Files:** `research/life_model.py`, `research/verify_life.py`, committed `apps/api/app/artifacts/hust-life-report.json`, `apps/api/app/artifacts/hust-curves.json`; `apps/api/app/research.py` (+ `/api/research/hust/report`, `/cells`, `/cells/{id}`), `apps/api/tests/test_research_hust.py`.
- [ ] Run; verify script recomputes metrics from per-cell predictions; API tests first (404 unknown, labels, counts 77) → implement → PASS; commit.

### Task 5: Research page
**Files:** `apps/web/app/research/page.tsx`, `apps/web/components/{ModelComparison,LifeScatter,CellCurves}.tsx`, `apps/web/lib/types.ts`, `apps/web/app/globals.css`.
- [ ] Build; screenshots 1440/390; fresh-clone render; commit.

### Task 6: Docs, review, PR
- [ ] MODEL_CARD rewrite (real numbers), DATA_SOURCES, LIMITATIONS, PLAN, README; full checks; opus code review; fixes; PR.
