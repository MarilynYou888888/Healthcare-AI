# Deterministic Clinic-Month investigation

This slice loads the five MVP logical datasets, calculates variances, selects
review targets, evaluates documented operating mechanisms, and produces a
traceable investigation result. It uses Python's standard library, with no model
API, frontend, external connector, database, or forecast write.

## Run

From the repository root with Python 3.10 or later:

```bash
python3 -m provider_fpa investigate \
  --inputs data/synthetic_benchmark/inputs \
  --clinic CL003 --month 2026-05 --target REV_NET_PATIENT

python3 -m provider_fpa benchmark --directory data/synthetic_benchmark

python3 -m unittest discover -s tests -v
```

Use `--type operational_metric_variance` or `--type forecast_assumption_variance`
to investigate an operating target. The Python entry point
`investigate_clinic_month(data, clinic_id, month)` returns every financial and
operational target for that Clinic-Month, including its review decision.

JSON decimals are lossless strings; percentages are fractional ratios, so
`"-0.12"` means -12%. Undefined numbers are `null`, with an explicit reason for
an unavailable percentage. Ratios are not rounded before materiality evaluation.
The benchmark compares its four-decimal gold ratios only at evaluation time.

## Architecture

```text
five CSV files → loading → immutable domain records
                              ↓
                         engine.investigate
                         ├─ calculations
                         ├─ review
                         ├─ drivers → timing
                         └─ InvestigationResult → presentation → JSON CLI

cases.json → evaluation → engine output compared with gold/*.json
```

- `models.py`: typed inputs, source references, driver taxonomy, epistemic states,
  timing evidence, and structured results. Primary-driver uniqueness is enforced.
- `loading.py`: exact aggregate-only CSV schemas, identity and source checks,
  Clinic references, dates, effective intervals, numeric normalization, and units.
  Duplicate rows or malformed schemas fail explicitly. Missing/invalid numeric
  inputs remain unavailable and can produce a Data Quality Issue investigation.
- `calculations.py`: signed actual minus comparator and signed ratio using
  `Decimal`; zero/missing denominators never produce a percentage.
- `review.py`: provider thresholds, critical metrics, effective dates, and
  explicit analyst override. Multiple applicable rules combine with OR.
- `drivers.py`: evidence-gated operating mechanisms and unique direct-driver
  selection. Rules use account/metric IDs, event types, dates, and values, never
  case IDs, Clinic IDs, or gold answers.
- `timing.py`: remaining approved forecast horizon or labeled next-three-month
  fallback; recurring is independent of temporary/structural classification.
- `evidence.py`: explicit state transitions and a separate human-confirmation
  entry point. Autonomous transitions cannot create Analyst-Confirmed Cause.
- `engine.py`: Clinic-Month scope, observed facts, calculations, review, driver
  assessment, timing, and source retention. It cannot read gold files.
- `presentation.py`: bounded explanations, analyst questions, and serialization.
- `evaluation.py`: independent seven-dimension gold comparison, source and fact
  validation, and structural predicates for forbidden conclusions.

The module separation follows the domain/service-layer approach described in
[Architecture Patterns with Python](https://www.cosmicpython.com/book/chapter_04_service_layer).
Decimal arithmetic follows [Python's accounting-oriented guidance](https://docs.python.org/3/library/decimal.html).
No additional framework is needed for this first local slice.

## Evidence and analytical boundaries

The revenue bridge must reconcile exactly in the current synthetic contract:
actual revenue = actual visits × actual revenue per visit, and the corresponding
forecast/expected bridge must also reconcile. Stable-rate volume misses require
documented operating support before becoming a Supported Driver. Arithmetic
alignment alone does not explain the operating cause of a visit shortfall.
This keeps C04 unresolved even though its corrected numerical bridge reconciles.

Provider constraints require both a documented event and lower aggregate
availability. Capacity constraints require an event and increased closure days.
Payer realization requires lower rate, changed payer mix, and a contract event.
Overtime requires an expense increase, higher overtime, and documented coverage
needs. Accounting timing requires a documented accrual amount matching the
expense variance; the subsequent reversal is retained when available.

A unique supported direct mechanism becomes primary. Supported upstream
mechanisms become contributing. External Disruption remains `upstream_context`,
matching the gold contract, rather than becoming a primary revenue driver.
Candidate, Rejected, and Unresolved hypotheses have `role: null`; this prevents
presenting an unsupported hypothesis as a primary/contributing conclusion.
Competing direct mechanisms are left unranked until additional evidence resolves
their precedence. No percentage contribution is generated. C07's documented
$20,000 accrual is the only benchmark amount allocation.

Every fact and conclusion retains a file, exact row selector, source, and the
available load/report timestamp. Event descriptions are reported source content,
not automatically accepted causal conclusions. Later loaded closed-month records
may corroborate earlier investigations: this is retrospective evaluation of the
provided snapshot, not an as-of historical replay.

`successful_investigation` reports workflow completion with evidence boundaries;
the evaluator independently scores correctness. C04 and C08 can therefore be
successful investigations with unresolved causes. A missing financial actual
cannot be reported as a successfully identified variance.

`successfully_explained_variance` additionally requires a driver promoted from
Supported to Analyst-Confirmed by an explicit `HumanDecision`, with no material
undisclosed issue. The engine never calls that promotion function. The local
human-review API records a review reference, timestamp, and rationale; authenticating
the human and persisting an audit trail belong to a later integration boundary.

## Explicit policies and remaining limits

- Thresholds use strict `>` to implement the locked glossary's “exceeded” rule.
  The existing benchmark generator uses `>=`; no current C01–C10 selection sits
  exactly at a threshold. Its selection behavior was left unchanged by the
  authorized rate correction.
- The approved horizon is represented by the input `forecast_horizon` event.
  An absent or exhausted horizon uses the next three months after the target
  month. Multiple eligible horizons fail as ambiguous rather than being guessed.
- “Material portion” currently means at least 50% of remaining horizon months;
  `classify_timing(..., material_fraction=...)` exposes that policy explicitly.
  Unknown/conflicting duration remains unresolved. Known finite event types use
  their documented endpoint as recovery evidence; arbitrary event types do not.
- Causal rules cover the benchmark's adverse revenue, labor-expense, and selected
  operating mechanisms. Favorable revenue and unmodeled accounts remain
  Candidate/Unresolved. The engine is not a universal financial attribution model.
- The benchmark's expected revenue-per-visit measure is treated as an embedded
  forecast assumption. Real exports will need explicit comparator/version and
  closed-month governance metadata before broader ingestion.
- The current revenue bridge is USD-based and exact. Currency conversion,
  production rounding tolerances, and complex netting are outside this slice.
- Event types are a controlled local vocabulary. Arbitrary prose is not parsed
  into causality; accrual extraction accepts the documented `USD … labor accrual`
  pattern. This is not a general natural-language reasoner.
- Forbidden-conclusion evaluation uses explicit structured predicates and a
  literal-claim check, not general semantic interpretation of arbitrary prose.
  Unrecognized gold prohibitions fail closed. Gold facts with no implemented
  semantic check also fail closed.
- All ten autonomous results require human review and remain unsuccessfully
  explained until the applicable human confirmation boundary is exercised.

## Fixture repair

The generator reconciles rates after scenario revenue/visit overrides. It does
not manually patch generated CSVs or infer C08's missing visits.

| Case/month | Old actual rate | Corrected actual rate | Expected rate |
| --- | ---: | ---: | ---: |
| C01 / March | 194 | 195 | 195 |
| C02 / April | 197 | 198 | 198 |
| C02 continuation / May | 197 | 198 | 198 |
| C02 continuation / June | 197 | 198 | 198 |
| C02 continuation / July | 199 | 198 | 198 |
| C02 continuation / August | 197 | 198 | 198 |
| C04 / June | 203 | 204 | 204 |

No gold fixture or case-manifest semantics changed. C08 remains the intentional
Data Quality Issue case. The fixed seed is still `20260907`; all 17 regenerated
files match an independent regeneration byte-for-byte. A regression test verifies
both actual and forecast revenue bridges wherever visits are present.

## Review artifacts

- [Seven-dimension benchmark results](validation/benchmark-results.json)
- [Full test output](validation/test-results.txt)

Recommended next slice, after review: persisted analyst decisions with explicit
confirmation/rejection, source-bound audit history, and recomputed Q12 success
states. No next feature has been started.

## Changed-file inventory

Modified existing files:

- `scripts/generate_synthetic_benchmark.py`
- `data/synthetic_benchmark/inputs/operational_values.csv`
- `tests/test_synthetic_benchmark_cli.py`

New engine files:

- `provider_fpa/__init__.py`
- `provider_fpa/__main__.py`
- `provider_fpa/models.py`
- `provider_fpa/loading.py`
- `provider_fpa/calculations.py`
- `provider_fpa/review.py`
- `provider_fpa/evidence.py`
- `provider_fpa/drivers.py`
- `provider_fpa/timing.py`
- `provider_fpa/engine.py`
- `provider_fpa/presentation.py`
- `provider_fpa/evaluation.py`

New tests:

- `tests/test_variance_calculations.py`
- `tests/test_review_rules.py`
- `tests/test_evidence_states.py`
- `tests/test_timing.py`
- `tests/test_loading.py`
- `tests/test_investigation.py`
- `tests/test_engine_boundaries.py`
- `tests/test_benchmark_evaluation.py`
- `tests/test_cli.py`

New documentation and validation artifacts:

- `docs/deterministic-investigation-engine.md`
- `docs/validation/benchmark-results.json`
- `docs/validation/test-results.txt`
