# Healthcare Provider FP&A Copilot

A local recruiting portfolio demo for healthcare provider FP&A / financial analysts. Driver-Based Scenario Modeling is primary; Evidence-Aware Variance Investigation is secondary.

## Run Ticket 1

```sh
python3 -m provider_fpa.web
```

Open http://localhost:8501/. Python 3.11+; no runtime packages, API keys or network connection required. Source links open the original SEC filings when internet is available. Stop with Ctrl-C.

This increment displays a calculated synthetic baseline and switches between read-only HCA and Tenet public context. Scenario editing, offline narrative, analyst review and investigation are subsequent approved tickets, pending review. No historical investigation business logic has been changed.

## Data and calculation boundaries

- `data/public_benchmarks/`: curated local filing extracts and source metadata, normalized by `provider_fpa/benchmark`. Each metric carries source page, extraction reference, raw scale, definition, reporting basis and source hash. Derived ratios retain both parent metric IDs and formula. Missing observations stay null.
- `data/synthetic/scenario/`: designer-selected monthly assumptions; no HCA/Tenet internal values. `provider_fpa/scenario` owns deterministic Decimal calculations and an immutable baseline. Public figures never become operands in this model.
- `provider_fpa/web.py` serves explicit read-only routes and static `web/` assets. Browser number formatting is presentation only.

The selected public extract has 48 HCA and 32 Tenet reported/missing records, plus ratios derived at load time. It is not a comprehensive data warehouse. Tenet same-hospital volumes must not be divided into full-segment financials; HCA admission payer mix differs from Tenet patient-service revenue mix. Hospital benchmarks supply context, not statistical validation of clinic assumptions or affiliation with either company.

The clinic's contribution margin is revenue less variable labor and supplies. Modeled operating income subtracts fixed clinic expense; it is not corporate GAAP net income. The model retains fractional expected visits and Decimal precision (28 significant digits); display rounds to two decimals. Baseline: 1,425.6 expected visits, $277,992 revenue, $173,923.20 contribution margin and $88,923.20 operating income.

## Verify

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q provider_fpa scripts tests
```

Browser acceptance uses optional Playwright and installed Google Chrome, against the running local app:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-browser.txt
.venv/bin/python scripts/check_browser.py
```

It checks public read-only presentation, both companies, source links, missing history, synthetic labels, baseline integrity, formulas, mobile overflow and isolated public-data failure. Screenshot defaults to `/tmp/provider-fpa-ticket1.png`.

## Reproduce source extracts

`python3 scripts/prepare_public_benchmarks.py` requires `openpyxl` and `pypdf`, plus the supplied HCA workbook and HCA/Tenet PDFs at the paths declared in that script. Extraction uses curated table mappings and numeric-token page checks; those checks are not independent semantic validation. The app uses committed extracts and never runs this script. Original source documents remain unchanged.
