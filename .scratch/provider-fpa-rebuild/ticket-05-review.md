# Ticket 5 validation and review

Scope: final recruiting-demo presentation only. Fixed point: `1668c3c` (pre-edit snapshot). Initial working commit: `f859ee1`; review command `git diff 1668c3c...f859ee1`, followed by a targeted review of the chart-range correction. No financial formulas, investigation rules, source datasets, review boundaries or ScenarioResult contracts were changed.

## Delivered outcome

- Consistent charcoal/off-white visual system with restrained gold accents, financial favorable/unfavorable colors, responsive navigation and full-session reset.
- Executive Summary with five KPIs, scenario driver, operating-income bridge, scenario expense donut, baseline/scenario financial comparison and separate visits measure.
- Shared `scenarioPresentation(ScenarioResult)` adapter computes presentation-only expense signs/cumulative bridge positions, composition shares and operating-margin ratios. Charts use this view and its source identity/revision, never recalculate operating outputs or write assumptions.
- Exact tooltips/text equivalents; 260 ms SVG geometry transitions; reduced-motion support. Zero expense produces an empty composition state; zero revenue produces N/A margin; negative income crosses a visible zero baseline. Invalid drafts clearly show the last valid results as stale with review disabled.
- Expandable trace reads the existing GRAPH, exposing input operands/results and highlighting downstream paths affected by changed assumptions.
- HCA/Tenet comparison uses the loader's existing consolidated labor/revenue and supplies/revenue ratios. Source definitions, parent IDs, reporting-basis caveats, FY2025/read-only labels and public/synthetic boundaries remain intact. No invented data or company-total-to-clinic allocation.
- Detailed model and income impact fit the 1440×900 recording viewport. Mobile uses contained chart/table scrolling rather than clipping the page.
- [Startup/reset instructions and 85-second talk track](../../docs/recruiting-demo.md).

## Actual validation

- Final full suite: 115 tests passed, including recovered investigation, scenario/interpretation/session review, chart arithmetic/signs, edge cases, revision binding, tooltip keyboard behavior, trace propagation, benchmark lineage/missing data and demo reset.
- Benchmark: 10/10 cases and 70/70 dimensions passed.
- Prior Ticket 1–4 browser scripts all passed, including offline scenario behavior, immutable public context, stale drafts, human-review invalidation, C01/C03 handoffs and C04 refusal.
- With all presentation consumers mounted: max input-to-painted-frame latency 33.7 ms across ten edits; zero recalculation requests. Chart geometry transitions are separately 260 ms; authoritative numbers update before that visual interpolation completes. Local headless Chrome measurement, not a universal device claim.
- Visual checks: 390, 768, 1024 and 1440 px widths; all three workspaces without document overflow. Desktop summary/model/composition/trace/benchmark screenshots inspected. The model's final income row initially fell below the reference viewport; tighter column widths and spacing corrected it without hiding calculations.
- Automated timed UI rehearsal: 85.0 seconds at 1440×900 with external requests blocked; all required scenario values and C04 human action checked. Intentional narration pauses included. This was not spoken audio, a recorded video, or hiring-manager validation. Report: `docs/validation/ticket5-rehearsal.json`.
- Python compile and Git whitespace checks passed. No configured static type checker.
- No diff in `web/scenario.js`, `web/scenario-view.js`, `web/interpretation.js`, recovered investigation business logic, synthetic assumptions or public benchmark data.

## Rehearsal feedback and limitations

The scenario cascade fits one recording screen; the summary, composition and trace need deliberate short scrolls documented in the talk track. C04's driver review card also requires a scroll after case selection. Read the offline disclosure aloud. Public ratios describe different company business mixes and Tenet continuing operations; they are directional context, not directly interchangeable clinic benchmarks. The prior guard-withheld operational-target narrative limitation remains unchanged. No measured business ROI, production readiness or live-AI claim is made.

## Standards

No documented standards violations or material recruiting-demo defects. One nonblocking numeric edge case was corrected: extremely large finite positive/negative endpoints could overflow an axis span. Both renderers now validate the span before generating geometry, use the existing unavailable-scale state, and recover after reset. A browser regression reproduced the failure and then passed; model validity is preserved.

Reviewer recheck: “No remaining findings from the Ticket 5 standards review.”

## Spec

No blocking findings. Five KPIs and all scenario visualizations use the same ScenarioResult; expense offsets, zero/negative/stale states, public lineage and session reset are correct. No financial formulas, assumptions or investigation rules changed. The automated 85-second timing remains explicitly distinct from spoken delivery or hiring-manager comprehension.

Final findings: Standards 0 remaining (1 edge case resolved); Spec 0. No remaining worst issue on either axis.
