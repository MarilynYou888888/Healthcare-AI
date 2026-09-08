# Provider FP&A Synthetic Benchmark

This directory is a deterministic, reproducible evaluation fixture for the
clinic-month Provider FP&A MVP. It tests analytical boundaries, not prose
quality. All organizations, clinics, values, and events are fictional.

## Generate and validate

From the repository root:

```bash
python3 scripts/generate_synthetic_benchmark.py \
  --output-dir data/synthetic_benchmark \
  --seed 20260907
```

The generator validates schemas, source fields, case and gold counts, all three
variance types, and every numeric Observed Variance before reporting success.
Run the independent test suite with:

```bash
python3 -m unittest discover -s tests -v
```

The fixed seed is `20260907`. Running the command twice with the same seed must
produce byte-identical files.

## Artifact contract

- `inputs/clinics.csv`: six fictional clinics and one market aggregation.
- `inputs/financial_values.csv`: clinic-month account actuals and Latest
  Approved Forecast values.
- `inputs/operational_values.csv`: clinic-month operating actuals and expected
  values.
- `inputs/operating_events.csv`: dated, source-attributed operating context.
- `inputs/review_rules.csv`: configurable absolute, percentage, and
  critical-metric rules. Materiality is not selected by an LLM.
- `cases.json`: the public 10-case manifest and review-queue selection metadata.
- `gold/C01.json` through `gold/C10.json`: system-hidden expected-answer
  fixtures. Do not expose these files to a system under evaluation.

Every input row carries a synthetic `source`. Value tables also carry a fixed
`loaded_at` timestamp so evidence provenance remains explicit and reproducible.

## Comparison and sign conventions

The core comparison is closed-month actual versus Latest Approved Forecast at
clinic x account or metric x month. Numeric variance is `actual - forecast` or,
for operating measures, `actual - expected`.

- Financial Variance: an account actual versus its approved forecast.
- Operational Metric Variance: an operating actual versus its expected value.
- Forecast Assumption Variance: an actual driver value versus the assumption
  embedded in the approved forecast.

A negative revenue variance is unfavorable; a positive expense variance is
unfavorable. Direction is explicit in gold fixtures rather than inferred from
the arithmetic sign alone.

## Expected-answer contract

Each gold fixture fixes seven scored dimensions:

1. Observed Variance
2. Expected Driver Family
3. Primary and Contributing Driver roles
4. Timing Classification
5. Epistemic State
6. Human Review Requirement
7. Forbidden Conclusion

Fixtures may also define an expected analyst question, an assumption-change
proposal, supported contribution estimate, and the two success criteria.
`Successfully Explained Variance` is a strict subset of `Successful
Investigation`; a correct unresolved result is successful investigation and is
not a successful explanation.

## Data boundary

No patient-level data is present. The benchmark contains only clinic-month
aggregates and dated operating context. It excludes names, dates of birth,
member IDs, claim IDs, encounter IDs, medical records, and claims-level PHI.
