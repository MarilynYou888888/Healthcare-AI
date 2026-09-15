# Healthcare Provider FP&A Copilot

A local recruiting portfolio demo for healthcare provider FP&A / financial analysts. Driver-Based Scenario Modeling is primary; Evidence-Aware Variance Investigation is secondary.

## Run the local demo

```sh
python3 -m provider_fpa.web
```

Open http://localhost:8501/. Python 3.11+; no runtime packages, API keys or network connection required. Source links open the original SEC filings when internet is available. Stop with Ctrl-C.

Ticket 2 adds an Excel-style Scenario Model: edit any of nine assumptions to update the complete baseline/scenario/change table immediately. Try Provider FTE 4.0 → 3.5. Executive Summary, offline narrative, analyst review and investigation remain later tickets, pending review. No historical investigation business logic has been changed.

## Data and calculation boundaries

- `data/public_benchmarks/`: curated local filing extracts and source metadata, normalized by `provider_fpa/benchmark`. Each metric carries source page, extraction reference, raw scale, definition, reporting basis and source hash. Derived ratios retain both parent metric IDs and formula. Missing observations stay null.
- `data/synthetic/scenario/`: designer-selected monthly assumptions; no HCA/Tenet internal values. `provider_fpa/scenario` loads immutable source assumptions only. `web/scenario.js` is the sole financial calculation engine and shared session store; the same graph calculates baseline and scenario. Public figures never become operands in this model.
- `provider_fpa/web.py` serves explicit read-only routes and static `web/` assets. Scenario arithmetic runs locally in the browser; edits make no network requests. `web/scenario-view.js` subscribes to immutable result revisions and formats them for display. Future summary/commentary consumers subscribe to that same result, without calculating it again.

The selected public extract has 48 HCA and 32 Tenet reported/missing records, plus ratios derived at load time. It is not a comprehensive data warehouse. Tenet same-hospital volumes must not be divided into full-segment financials; HCA admission payer mix differs from Tenet patient-service revenue mix. Hospital benchmarks supply context, not statistical validation of clinic assumptions or affiliation with either company.

The clinic's contribution margin is revenue less variable labor and supplies. Modeled operating income subtracts fixed clinic expense; it is not corporate GAAP net income. The model retains fractional expected visits and Decimal precision (28 significant digits, half-even rounding); display rounds to two decimals. Baseline: 1,425.6 expected visits, $277,992 revenue, $173,923.20 contribution margin and $88,923.20 operating income.

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
```

It checks public read-only presentation, both companies, source links, missing history, synthetic labels, baseline integrity, formulas, mobile overflow and isolated public-data failure. It also tests the one-input cascade, reset, stale invalid drafts, all nine dependencies, shared-result identity and measured input-to-painted-frame latency with network requests blocked. Screenshot defaults to `/tmp/provider-fpa-ticket2.png`.

## Reproduce source extracts

`python3 scripts/prepare_public_benchmarks.py` requires `openpyxl` and `pypdf`, plus the supplied HCA workbook and HCA/Tenet PDFs at the paths declared in that script. Extraction uses curated table mappings and numeric-token page checks; those checks are not independent semantic validation. The app uses committed extracts and never runs this script. Original source documents remain unchanged.


## Scenario state contract

`createScenarioStore(source)` exposes `snapshot()`, `subscribe(listener)`, `edit(id, rawString)` and `reset()`. The session snapshot includes draft assumptions, a monotonically increasing revision, validation errors, `result`, `last_valid`, and `review_eligible`. Invalid drafts have `result: null` and cannot supply a current reviewable result. The UI labels the last valid snapshot as stale. Reloading resets the session.

`ScenarioResult` carries synthetic provenance, model version, baseline identity/Clinic-Month, all baseline/scenario assumptions and outputs, units, changed drivers, absolute/percentage changes and hypothetical monthly impact. Percentages are N/A for zero or negative baselines, with a reason. No forecast is approved or written. Later Executive Summary and narrative/review must consume the same result revision.

The pinned MIT-licensed decimal.js 10.6.0 module and license are vendored under `web/vendor/`; no CDN or package download is needed at runtime. Its 28-digit, half-even configuration matches the previous Python model. Calculation-location migration is documented in Ticket 2; business formulas are unchanged.
