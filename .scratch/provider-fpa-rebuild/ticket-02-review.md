# Ticket 2 review

Scope: Change One Driver and See Financial Impact, including the approved one-model/two-presentations clarification. Fixed point c85f8e3; initial working commit 066d814. Review compared `git diff c85f8e3...066d814`, followed by targeted recheck of shared-store input synchronization.

## Standards

No documented standards violations or material correctness findings. The engine owns financial calculations and state; the view presents snapshots; Python loads assumptions without repeating formulas.

Initial nonblocking integration observation: programmatic store changes updated results but not visible assumption fields. Resolved by synchronizing subscribed draft values while preserving active text/caret when unchanged. Reset uses the same path. Added a failing-then-passing browser regression.

Reviewer recheck: “No remaining observations from the Ticket 2 standards review.”

The prior historical ADR/CONTEXT scope conflict remains governed by the later approved specification. No new domain conflict.

## Spec

Reviewer: “No blocking findings.”

FTE 4.0→3.5 derives every reference output and the −$21,740.40 impact. All nine dependency paths, immutable baseline, coherent deltas, reset, changed inputs, invalid/stale states and N/A percentage reasons are covered. The documented browser migration preserves formulas and Decimal policy while removing recalculation network calls. The shared immutable revisioned result supports future summary and commentary consumers without duplicated arithmetic.

Executive Summary, narrative/review and investigation remain deferred to their approved tickets. No financial business-logic deviation found.

## Validation

18 tests passed in the full suite. Chrome browser acceptance passed: editable cells, complete dependency cascade, baseline integrity through HCA/Tenet switching, public lineage/missing data, formula visibility, zero-network recalculation, stale invalid drafts, reset, percent input display, mobile overflow and public-reference failure isolation. Desktop screenshot visually inspected at 1440px width.

Final measured input-to-painted-frame samples (ms): 26.5, 33.2, 32.5, 34.2, 33.3, 33.4, 33.3, 33.4, 32.9, 33.3. Maximum 34.2 ms; target 200 ms. Zero recalculation requests. Measurement includes two animation frames; headless Chrome on the local demo machine, not a guarantee for every device.

Python compile and git whitespace checks passed. No static type checker is configured. Spreadsheet reference was read-only; its formulas were not imported.

Final findings: Standards 0 remaining (1 observation resolved); Spec 0 blocking. No remaining worst issue on either axis.
