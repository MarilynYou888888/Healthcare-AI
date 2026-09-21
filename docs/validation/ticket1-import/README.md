# Ticket 1 implementation review

Date: 2026-09-21. Scope: Self-Service Data Import & Validation only. Awaiting user review. Tickets 2–4 have not started.

## Review the complete workflow

Start the existing local server with `python3 -m provider_fpa.web` and choose **Import My Data** from the sidebar, or visit `/import`. The review session started by the agent is at http://localhost:8502/import while that process remains running.

1. Choose an ordinary CSV/XLSX or download the optional sample workbook.
2. Assign a role to each desired sheet and select its header row. Other sheet names and column names are supported.
3. Review suggested column mappings. The sample demonstrates FTE Count → Provider FTE, Work Days → Operating Days, and Rev / Visit → Net Revenue / Visit. Select percentage-point encoding for its utilization column.
4. Validate. ERROR blocks confirmation, WARNING requires acknowledgment, and INFO records exclusions and transformations. Errors include source row/column and correction guidance.
5. Compare original and normalized tables and inspect the complete paginated normalization register. Sample utilization 90 becomes the exact decimal 0.9 (90%).
6. Explicitly confirm. Existing roles require separate replacement consent. Failed validation never replaces confirmed data.
7. Inspect confirmed session datasets. No analytical engine is initialized from imports in Ticket 1. Leaving/reloading the page discards the session; V1 demo data remains independent.

The optional workbook includes Planning Assumptions (3 rows), Actual vs Forecast (3 rows), and Operating Events (1 row), all synthetic. An exact content fingerprint identifies the bundled example; arbitrary uploaded source text does not establish built-in provenance. Users need not follow its filename, sheet names, or headers.

## Visual evidence

- [Upload and privacy notice](01-upload-desktop.png)
- [Sheet roles and preview](02-sheet-roles.png)
- [Column mapping](03-column-mapping.png)
- [Validation](04-validation.png)
- [Original and normalized previews](05-original-normalized-preview.png)
- [Normalization register](06-normalization-register.png)
- [Confirmed session datasets](07-confirmed-session.png)
- [Errors with prior data preserved](08-errors-preserve-session.png)
- [Mobile validation](09-mobile-validation.png)
- [Mobile upload](10-mobile-upload.png)

Inspected desktop 1440×1000 and mobile 390×844. Tables scroll within the page; no horizontal page overflow or browser errors. The workbook's three sheet previews were also rendered and inspected during authoring.

## Validation results

- `python -m unittest discover -s tests -v`: **141 passed** (116 existing + 25 Ticket 1), 19.737 seconds.
- Ticket 1 tests: CSV quoting/BOM/encoding; XLSX and custom sheet/header names; multi-role sample; aliases/collisions/manual correction; required/numeric/date/sign/currency/unit checks; percent encoding including native Excel percentages; duplicate detection; missing mapped cells and explicit constants; formula caches/merged cells; row/column/populated-cell/file/expanded-archive bounds; dishonest ZIP sizes; cancellation/timeouts; atomic replacement and immutability; no upload/external requests or persistent browser storage; page exit/reload behavior.
- `scripts/check_import.py`: passed; [machine-readable rehearsal](rehearsal.json). Zero external requests, zero upload requests, no page errors, failed replacement preserves data, refresh discards session.
- Existing `scripts/check_browser.py`: passed; V1 public benchmarks and baseline/scenario cascade preserved. Maximum measured recalculation-to-paint latency 34.4 ms, zero recalculation network requests.
- Python compilation, JavaScript syntax checks for all four new modules, and `git diff --check`: passed.
- Existing scenario formulas, public benchmark files/loaders, synthetic inputs, and investigation engine files have no changes.

## Standards review

The required independent standards review initially found a timestamp-provenance issue and a resource-policy duplication heuristic. Excel timestamps without a timezone now require explicit ISO timestamp input instead of inventing UTC midnight. Parser and UI limits now share one definition. The focused recheck found both issues resolved and no remaining documented-standard breach or immediate blocker. Reviewers inspected code; test execution was performed by the implementing agent.

## Spec review

The independent spec review initially found a missing mapped-cell fallback to constants, incomplete mixed-percentage checks outside utilization, and the timestamp issue. Regression tests reproduced each failure before fixes. Mapped missing cells now remain missing, mixed-scale checks cover ratios across all roles, and ambiguous reporting timestamps block. The focused recheck found all findings resolved and no immediate additional blocker or Ticket 2–4 scope creep.

## Scope and limitations

No intentional deviation from the approved Ticket 1 financial/privacy boundaries. There is no upload endpoint, external API, LLM, key, paid dependency, or persistence. Dependencies are vendored locally with licenses and hashes. Browser bytes and normalized data stay in page/worker memory; this ticket does not use the planned Ticket 2 loopback investigation adapter.

This delivery is the linked import workspace, not the Ticket 4 landing redesign or Clear Uploaded Data feature. Ticket 2 alone will connect confirmed imports to analytical screens. Benchmark selection and commentary remain for Ticket 3; report export remains for Ticket 4.

Use UTF-8 CSV or an unencrypted XLSX with one rectangular table per sheet. Resource ceilings also protect workbook parsing before sheet-role selection. No macro/formula execution or external workbook links. Cached formula values require review; unknown cache freshness is disclosed. Excel reporting timestamps without a timezone must be supplied as timezone-bearing ISO text or left unknown. The personal-identifier header guard is not a PHI detector or de-identification service.

## Changed files

- `web/import.html`, `web/import.css`: professional local import workspace.
- `web/import-view.js`: visible workflow, previews, explicit confirmation, and page lifecycle.
- `web/import-schema.js`: four roles, alias dictionary, metric vocabulary, and shared limits.
- `web/import-validation.js`: explicit normalization, validation, immutable session data.
- `web/import-worker.js`: cancellable bounded local CSV/XLSX parsing.
- `web/sample-import.xlsx`: optional three-sheet synthetic onboarding example.
- `web/vendor/xlsx.full.min.js`, `web/vendor/papaparse.min.js`, their license files, and `web/vendor/import-libraries.md`: pinned local parsers with provenance.
- `web/index.html`: one import-workspace sidebar link; V1 behavior preserved.
- `provider_fpa/web.py`: explicit static routes only; no upload endpoint.
- `tests/test_import.py`: 25 Ticket 1 browser/contract tests.
- `scripts/check_import.py`: repeatable visual/acceptance rehearsal.
- Ticket 1 issue: acceptance completion and review handoff.
- This validation directory: review report, rehearsal JSON, and ten screenshots.

## Rollback

Pre-implementation snapshot: `9e6a2f5`. Working implementation checkpoint: `aaeb353`. Final review fixes and evidence are committed separately. Existing unrelated untracked user files were not modified or committed.
