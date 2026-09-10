# Phase 4 AI Narrative Layer

Phase 4 consumes one validated `InvestigationResult` from the deterministic
Clinic-Month engine and renders concise management commentary. It does not own
calculations, materiality, driver assignment, timing, evidence state, or
forecast changes.

```text
Clinic-Month inputs
  → provider_fpa.engine.investigate
  → InvestigationResult
  → provider_fpa.narrative.generate_narrative
  → typed NarrativeOutput / management commentary
```

`NarrativeInput` contains only the validated result. `build_prompt` serializes
that structured result and explicitly instructs the one provider adapter,
`OpenAINarrativeProvider`, to return the seven required sections. The adapter
accepts an injected transport so tests remain offline. When no transport is
configured, or a provider request fails, `DeterministicNarrativeFormatter`
produces the same sections without an API key.

The output sections are Executive Summary, Key Variances, Supported Drivers,
Evidence Gaps / Unresolved Drivers, Questions for Operations, Forecast
Considerations, and Human Review Required. The fallback uses only values and
states already present in the result. It never assigns Analyst-Confirmed Cause,
estimates unsupported contribution percentages, removes unresolved status, or
writes forecast assumptions.

`validate_narrative` is the acceptance boundary for both fallback and provider
wording. It checks Clinic-Month identity, required section order, provider name,
human-review status, successfully-explained status, deterministic numeric tokens,
driver family/role/state labels, unsupported percentage signs, confirmation
language, autonomous forecast-change language, and unresolved evidence phrases.
It rejects a provider response rather than silently repairing it. The fallback
is used only for unavailable provider transport/schema errors.

The exact local demo command is:

```bash
python3 -m provider_fpa narrative \
  --inputs data/synthetic_benchmark/inputs \
  --clinic CL001 --month 2026-03 --target REV_NET_PATIENT
```

The C03 command is identical with `CL003`, `2026-05`; C04 uses `CL004`,
`2026-06`. The benchmark remains available through the Phase 3 evaluator:

```bash
python3 -m provider_fpa benchmark --directory data/synthetic_benchmark
```

All tests use mocked transport only. No API key, external connector, frontend,
RAG, or multiple-provider routing is included in this slice.
