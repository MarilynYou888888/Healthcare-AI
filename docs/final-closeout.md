# Final project closeout

Date: 2026-09-16. All five approved tickets are complete. No new product features or financial formula changes were introduced during closeout.

## Final validation

- Complete suite: **116 tests passed**, including a new extreme-input safety regression (first reproduced failing, then passing).
- Investigation evaluator: **10/10 cases, 70/70 dimensions passed**.
- Four browser smoke scripts passed: `check_browser.py`, `check_interpretation.py`, `check_investigation.py`, `check_presentation.py`.
- Input-to-painted-frame maximum: **33.5 ms** across ten measurements, with **zero recalculation network requests**.
- Responsive checks: **390, 768, 1024, 1440 px**; no page errors. Keyboard navigation/tooltips, stale state and reduced-motion checks passed. Desktop and mobile screenshots inspected.
- Python compilation and `git diff --check` passed.
- Recruiting flow: automated **85-second UI rehearsal** passed without audio/video recording. This validates the scripted interactions, not spoken narration or hiring-manager comprehension.

## End-to-end acceptance

| Area | Verified outcome |
|---|---|
| Scenario | Both public companies load read-only. Synthetic baseline stays immutable. FTE 4.0 → 3.5 propagates through every dependency. |
| Executive Summary | KPIs, comparisons and charts consume the shared result revision. No second operating model. Operating margin uses operating income / revenue; zero revenue yields N/A. |
| Bridge | $88,923.20 baseline − $34,749 revenue + $9,801 labor savings + $3,207.60 supply savings + $0 fixed-expense impact = $67,182.80 scenario. Net impact −$21,740.40 is derived, never hard-coded. |
| Expense mix | $68,607 labor + $22,453.20 supplies + $85,000 fixed = $176,060.20 scenario operating expense. |
| Trace | Relationships and affected paths come from the engine's graph. Charts map presentation measures to geometry, without recomputing operating outputs. |
| Commentary | Explicit offline fallback disclosure; consumes current deterministic results. Invalid drafts suppress commentary and disable review. No live generation or forecast write. |
| Investigation | C01 supported; C04 unresolved without evidence; C03 weather is upstream context, with volume/capacity as financial/operating drivers. Only human actions confirm supported causes. |
| Handoff | Opens/highlights a related assumption and preserves evidence context; does not modify inputs, result revision, scenario review, or forecast. |

## Data integrity and lineage

All **99 loaded public records** retain company, period, definition, unit, source document, URL, locator and hash: HCA has 48 reported records plus 11 derived ratios; Tenet has 32 reported/missing records plus 8 derived ratios. Tenet FY2023 adjusted admissions remain missing for the selected cohort, with a reason; no historical value was inferred. Derived ratios preserve their source operands and reporting basis.

The two public source URLs correspond to [HCA's FY2025 filing](https://www.sec.gov/Archives/edgar/data/860730/000119312526044769/hca-20251231.htm) and [Tenet's FY2025 filing](https://www.sec.gov/Archives/edgar/data/70318/000007031826000012/thc-20251231.htm). Tenet content was retrieved; HCA was verified through indexed SEC filing content and its filing directory. Direct automated HCA HEAD access returned 403, and full web extraction exceeded the tool's size limit. These access restrictions are not evidence of a broken URL; live SEC availability cannot be guaranteed. The application uses local extracts and does not depend on external links loading.

Application datasets contain public company aggregates and explicitly synthetic clinic/case records, not PHI or proprietary planning data. Public metrics never become clinic-model inputs. No fictional monthly trend was added. Hospital benchmarks are context, not proof that specific clinic assumptions are empirically calibrated. Comparability caveats remain visible. No affiliation, sponsorship or internal access is implied. User-authored proposal/image files were preserved and are outside this application-data audit.

## Standards review

Cumulative review from pre-Ticket-1 snapshot `a2061db` found one clear input-validation defect: enormous finite Decimal exponents could exhaust browser memory during fixed-point formatting. Closeout adds technical limits of 128 input characters and exponent magnitude 1000 for assumptions and derived operating outputs. The shared store rejects unsafe drafts, preserves stale last-valid results, disables review, and recovers after correction. Financial formulas, rounding policy and the approved reference outputs remain unchanged. The fix was re-reviewed with no remaining actionable findings.

The durable approach bounds data before rendering, rather than catching a failed chart after formatting. Its cost is rejection of extreme inputs outside the demo's supported numeric range. This follows the resource implications documented by [decimal.js](https://mikemcl.github.io/decimal.js/#toFixed); it is not a financial planning constraint.

No additional clear defects were found in financial-logic duplication, hard-coded results, stale state, formatting, obsolete code, unsafe rendering, accessibility or responsive behavior. Automated checks and inspection are not a formal accessibility/security certification.

## Spec review

Independent review found no missing core acceptance requirements. Public/synthetic boundaries, one-result architecture, evidence states, session-only review and non-mutating handoff remain consistent with the approved scope. Earlier proposal-stage metadata and historical variance-first domain notes are archival; approved ticket framing supersedes them.

## Final modules and documents

| Responsibility | Location |
|---|---|
| Public lineage, normalization and curated extracts | `provider_fpa/benchmark/`, `data/public_benchmarks/` |
| Synthetic baseline and authoritative model/store | `provider_fpa/scenario/`, `data/synthetic/scenario/`, `web/scenario.js` |
| Detailed model and executive presentation | `web/scenario-view.js`, `web/executive.js`, `web/presentation.js`, `web/charts.js`, `web/benchmark-view.js` |
| Offline scenario interpretation/review | `web/interpretation.js` |
| Evidence engine, guarded narrative and adapter | `provider_fpa/engine.py`, `provider_fpa/narrative.py`, `provider_fpa/investigation.py`, `web/investigation.js` |
| Local server and navigation/style | `provider_fpa/web.py`, `web/app.js`, `web/index.html`, `web/style.css` |
| Verification and recording instructions | `tests/`, `scripts/check_*.py`, `scripts/rehearse_recruiting_demo.py`, `docs/recruiting-demo.md` |

Closeout changes only `.gitignore`, `README.md`, this report, `web/scenario.js` validation, and its regression in `tests/test_scenario.py`. `.DS_Store` is ignored. The user proposal and two images remain untracked and untouched; no project documents were deleted.

## Remaining limitations and recording readiness

Ready for the user's portfolio recording at the reference 1440×900 viewport. The app intentionally models one synthetic clinic/month; commentary is offline; review is session-only. No forecast is approved or persisted. The historical narrative guard withholds prose for 40 of 89 additional operational targets; all ten primary case narratives pass. The 50% structural timing threshold remains a configurable demo heuristic, not an industry standard. These limitations are disclosed and do not block the primary demo.

Use the existing 85-second guide: public grounding → FTE edit → deterministic cascade → summary/bridge → model trace → disclosed commentary → C04 unresolved → human judgment. No video was recorded during closeout.

```sh
cd "/Users/muhanyou/Desktop/Healthcare AI"
python3 -m provider_fpa.web
```

Open **http://localhost:8501/**. At closeout the server was already listening on port **8501**; do not launch a duplicate while it is running. Stop with Ctrl-C in its owning terminal when appropriate.
