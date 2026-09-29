# Healthcare Provider FP&A Copilot

A local recruiting portfolio demo for healthcare provider FP&A / financial analysts. Driver-Based Scenario Modeling is primary; Evidence-Aware Variance Investigation is secondary.

Public context comes from **HCA Healthcare and Tenet Healthcare FY2025 public filings**, clearly separated from **synthetic clinic-level planning assumptions**. Public actuals are read-only and never become scenario inputs.

**Deterministic financial calculations → explicitly disclosed interpretation → human analyst judgment.** The demo uses offline fallback commentary, not live AI generation. This is a portfolio demonstration, with no affiliation, sponsorship, or internal-data access implied for HCA Healthcare or Tenet Healthcare.

## Run the local demo

```sh
cd "/Users/muhanyou/Desktop/Healthcare AI"
python3 -m provider_fpa.web
```

Open http://localhost:8501/. Python 3.11+; no runtime packages, API keys or network connection required. Source links open the original SEC filings when internet is available. Stop with Ctrl-C. The landing controls separate **Explore Demo** from **Use My Data**; uploaded CSV/XLSX files remain in browser memory for the session.

The app opens on Executive Summary. Switch to Scenario Model and edit Provider FTE 4.0 → 3.5; the calculation table, summary and offline commentary share one result revision. Record one of three session-only analyst decisions. Variance Investigation is available as the secondary workspace; the Executive Summary now includes the income bridge, expense mix, financial comparisons and model trace. Recovered investigation rules and approved scenario formulas are preserved.

## Data and calculation boundaries

- `data/public_benchmarks/`: curated local filing extracts and source metadata, normalized by `provider_fpa/benchmark`. Each metric carries source page, extraction reference, raw scale, definition, reporting basis and source hash. Derived ratios retain both parent metric IDs and formula. Missing observations stay null.
- `data/synthetic/scenario/`: designer-selected monthly assumptions; no HCA/Tenet internal values. `provider_fpa/scenario` loads immutable source assumptions only. `web/scenario.js` is the sole financial calculation engine and shared session store; the same graph calculates baseline and scenario. Public figures never become operands in this model.
- `provider_fpa/web.py` serves explicit data routes, a stateless session-review endpoint, and static `web/` assets. Scenario arithmetic runs locally in the browser; edits make no network requests. `web/scenario-view.js` subscribes to immutable result revisions and formats them for display. Summary, charts and commentary consume that same result, without calculating operating outputs again.

The selected public extract has 48 HCA and 32 Tenet reported/missing records, plus ratios derived at load time. It is not a comprehensive data warehouse. Tenet same-hospital volumes must not be divided into full-segment financials; HCA admission payer mix differs from Tenet patient-service revenue mix. Hospital benchmarks supply context, not statistical validation of clinic assumptions or affiliation with either company.

The clinic's contribution margin is revenue less variable labor and supplies. Modeled operating income subtracts fixed clinic expense; it is not corporate GAAP net income. The model retains fractional expected visits and Decimal precision (28 significant digits, half-even rounding); display rounds to two decimals. Baseline: 1,425.6 expected visits, $277,992 revenue, $173,923.20 contribution margin and $88,923.20 operating income.

## V2 local workflow and export

Choose **Use My Data** to upload aggregated, de-identified CSV/XLSX data, assign sheet roles, map columns, validate, preview normalization, and explicitly confirm the session import. Planning-only data enables Scenario Model and Executive Summary; Actual vs Forecast data enables Variance Investigation. Operating Events alone never creates a variance target. **Clear Uploaded Data** removes browser-session datasets, drafts, notes, reviews, and pending import work, then returns to **Explore Demo**; built-in public and synthetic files are unchanged. **Reset Scenario** only resets the selected scenario draft.

The uploaded workspace can export the current valid `ScenarioResult` as a lightweight CSV. It includes source disclosure, assumptions, outputs, changes, deterministic Automated FP&A Commentary, and a separately labeled Analyst Note. Export is generated in the browser; no report file is written to the server. The core commentary is complete rule-based functionality with zero LLM tokens, API keys, paid APIs, external AI-provider accounts, or paid cloud inference.

Payer Mix / Reimbursement Drivers is an optional uploaded context role. Wide payer columns are normalized into payer-category records and checked against a 100% entity-period total. Payer mix without payer-specific reimbursement remains context only. A blended Net Revenue / Visit is calculated only when complete payer-specific values are present and the analyst explicitly selects **Use payer-mix-derived Net Revenue / Visit**; the existing Scenario Model remains the downstream source of revenue and operating-income calculations.

## Verify

```sh
.venv/bin/python -m unittest discover -s tests -v
python3 -m compileall -q provider_fpa scripts tests
```

The full suite uses Playwright and installed Google Chrome to exercise the authoritative browser engine; there is no duplicate Python financial model. Install test dependencies once:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-browser.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_browser.py
.venv/bin/python scripts/check_interpretation.py
```

It checks public read-only presentation, both companies, source links, missing history, synthetic labels, baseline integrity, formulas, mobile overflow and isolated public-data failure. It also tests the one-input cascade, reset, stale invalid drafts, all nine dependencies, shared-result identity and measured input-to-painted-frame latency with network requests blocked. Screenshot defaults to `/tmp/provider-fpa-ticket2.png`.

## Reproduce source extracts

`python3 scripts/prepare_public_benchmarks.py` requires `openpyxl` and `pypdf`, plus the supplied HCA workbook and HCA/Tenet PDFs at the paths declared in that script. Extraction uses curated table mappings and numeric-token page checks; those checks are not independent semantic validation. The app uses committed extracts and never runs this script. Original source documents remain unchanged.


## Scenario state contract

`createScenarioStore(source)` exposes `snapshot()`, `subscribe(listener)`, `edit(id, rawString)` and `reset()`. The session snapshot includes draft assumptions, a monotonically increasing revision, validation errors, `result`, `last_valid`, and `review_eligible`. Invalid drafts have `result: null` and cannot supply a current reviewable result. The UI labels the last valid snapshot as stale. Reloading resets the session.

`ScenarioResult` carries synthetic provenance, model version, baseline identity/Clinic-Month, all baseline/scenario assumptions and outputs, units, changed drivers, absolute/percentage changes and hypothetical monthly impact. Percentages are N/A for zero or negative baselines, with a reason. No forecast is approved or written. Executive Summary and narrative/review consume the same result revision.

The pinned MIT-licensed decimal.js 10.6.0 module and license are vendored under `web/vendor/`; no CDN or package download is needed at runtime. Its 28-digit, half-even configuration matches the previous Python model. Calculation-location migration is documented in Ticket 2; business formulas are unchanged.


## Executive Summary and interpretation

`web/executive.js` renders the same result as the detailed model. `web/interpretation.js` formats validated current results only and owns a separate revision-bound review session. It accepts no live provider text, performs no financial arithmetic, and exposes no forecast write. The UI explicitly states: “Rule-based commentary from calculated results and recorded evidence. No LLM or external API is used.”

Review choices: Reviewed — retain baseline; Request further investigation; Mark for forecast-assumption review. Any model edit (including an invalid draft) or reset clears the decision. Navigation preserves it; reload creates a new session. Invalid inputs remove commentary and disable review while the numerical views label the last valid revision as stale. Neither localStorage nor sessionStorage is used.

Phase 4 reuse is limited to inspected result-bound immutable formatting and human-review patterns from historical commit `40e4829`. Investigation actual/comparator contracts and live-generation transports were not imported into the hypothetical scenario workflow.

### Shared presentation sections

Ticket 5 fills the original stable sections without moving model state or recreating the calculation engine:

| Section | Existing content | Chart mount |
|---|---|---|
| `summary-kpis` | Five KPIs, baseline/scenario/deltas | Operating-margin KPI via the shared presentation adapter |
| `summary-impact` | Monthly income impact and endpoint values | `income-bridge-chart` |
| `summary-analysis` / `summary-comparison` | Financial comparison values | `scenario-comparison-chart` |
| `summary-analysis` / `summary-expenses` | Three expense categories | `expense-mix-chart` |
| `summary-model-logic` | Expandable formula trace | Affected dependency path from the existing GRAPH |
| `summary-commentary` / `summary-review` | Offline narrative and session decisions | Preserve revision binding |

`web/presentation.js` derives bridge signs, expense shares and margin presentation measures from the existing result. `web/charts.js` maps those values to SVG geometry; the presentation adapter reads the existing GRAPH for trace relationships. Neither calls the financial calculator or writes to the store. The approved financial formulas remain unchanged. Public comparison uses existing source-linked ratios through `web/benchmark-view.js`, never clinic assumptions.


## Variance Investigation (Ticket 4)

Open **Variance Investigation** and select a synthetic Clinic-Month. C01 (Provider PTO), C04 (unresolved volume miss), and C03 (weather/closure) are the recruiting cases. All ten benchmark cases remain available. The Review Queue is calculated from actual review rules, including critical metrics; its selector also exposes targets below the rules for explicit **Analyst Override**.

Expand observed facts to inspect input filenames, row identities, sources and timestamps. Driver cards distinguish the immutable system assessment from the current analyst decision. Supported is not confirmed. Use **Confirm supported cause**, **Reject cause**, **Keep unresolved**, or **Request further investigation**. Confirmation requires an originally supported driver; observed upstream context cannot be promoted to a cause. A request records a follow-up without inventing evidence. New choices replace the prior session choice for that driver. Review decisions are in page memory only, scoped to an evidence snapshot and target; tab navigation preserves them, page reload clears them. No approval is persisted or authenticated.

**Explore Provider FTE** in C01 or **Explore Clinic operating days** in C03 opens the existing Scenario Model and highlights the related input. The banner preserves case, Clinic-Month, driver, state and source context. It does not change an input, model revision, scenario review decision, or approved forecast. C04 offers no fabricated causal handoff.

Historical Phase 3/4 code and 73 tests were recovered from `ceb51b3`. The only integration change to historical engine code forwards its already-configurable timing threshold; default remains 0.5. Configure it in `data/synthetic/investigation_policy.json`. It is a demo policy, not a healthcare FP&A standard. Recurrence remains independent of persistence.

`provider_fpa/investigation.py` adapts immutable results for the web. It loads the five input CSVs and case identity fields only; neither analysis nor narration reads gold answers. The recovered narrative guard is unchanged. Some additional operational targets fail that guard; their prose is explicitly withheld while facts, review selection and Analyst Override remain accessible. All ten main case narratives pass. Human decisions are shown separately and never fed back into system narration.

Run the ten-case evaluator separately:

```sh
python3 -m provider_fpa benchmark --directory data/synthetic_benchmark
.venv/bin/python scripts/check_investigation.py
```

The historical domain/ADR descriptions of variance as the initial MVP are retained as recovery context; the approved specification supersedes that product framing. Driver-Based Scenario Modeling remains the primary recruiting demo. No historical Streamlit UI or old production scaffolding was restored.


## Record the recruiting demo

See [the 85-second walkthrough and recording guide](docs/recruiting-demo.md). The charcoal/off-white/gold presentation includes responsive charts, keyboard tooltips, reduced-motion support and a complete demo-session reset. The reference recording viewport is 1440×900. Financial comparisons are one month, baseline versus scenario; no time-series data has been invented. Run `scripts/rehearse_recruiting_demo.py` for the timed browser rehearsal.


## Final closeout

See [final acceptance, review, and validation results](docs/final-closeout.md). All five tickets are complete. The application remains a local, one-clinic / one-month demonstration with session-only review state.

Numeric validation includes technical resource limits: at most 128 input characters and base-10 exponent magnitude of 1000 for assumptions and derived operating outputs. These are browser-safety limits, not financial planning rules. Unsafe drafts retain explicitly stale last-valid outputs, suppress commentary, and disable review until corrected.

Run the remaining presentation checks against the running app:

```sh
.venv/bin/python scripts/check_presentation.py
.venv/bin/python scripts/rehearse_recruiting_demo.py
```

The timed rehearsal exercises the UI without recording audio or video. It does not replace your narrated recording.
