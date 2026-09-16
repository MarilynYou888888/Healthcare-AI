# Healthcare Provider FP&A Copilot — recruiting demo

Driver-Based Scenario Modeling is the primary workflow. Evidence-Aware Variance Investigation is secondary. This is a local portfolio demonstration, not an internal HCA/Tenet planning system.

## Start and reset

From `/Users/muhanyou/Desktop/Healthcare AI`:

```sh
python3 -m provider_fpa.web
```

Open **http://localhost:8501/** in Chrome. Use a **1440 × 900** browser content viewport at 100% zoom for the reference recording. A larger viewport also works. No API key, live filing fetch, database or internet connection is required; source links need internet only if opened.

Choose **Reset demo session ↻** in the header before each take. It reloads the local page, restoring FTE 4.0, the fixed synthetic baseline, HCA selection, collapsed trace and fresh scenario/investigation review states. **Reset to baseline** resets scenario assumptions/review only; it does not erase investigation decisions. Stop the server with Ctrl-C.

## 85-second talk track

| Time | Show / action | Suggested narration |
|---|---|---|
| 0–8 s | Executive Summary, baseline, disclosure strip | “This helps healthcare FP&A analysts connect operating assumptions to financial results, reducing the manual work of updating models and explaining changes.” |
| 8–16 s | Click **PUBLIC HCA + Tenet · FY2025**; show normalized comparison | “HCA and Tenet public filings provide context. The editable clinic assumptions are synthetic; these are not company forecasts.” |
| 16–22 s | Open **Scenario Model**, point to Provider FTE 4.0 | “This is one clinic and one month, with a fixed baseline and editable operating assumptions.” |
| 22–30 s | Change only Provider FTE to **3.5** | “One change updates capacity, visits, revenue, labor, supplies, contribution margin and operating income automatically.” |
| 30–42 s | Open **Executive Summary**; point to bridge | “Monthly revenue falls about $34.7 thousand. Variable cost savings partly offset that decline, leaving $21.7 thousand of operating-income downside.” |
| 42–48 s | Scroll to financial comparison and donut | “The same results feed the management view. Fixed costs remain unchanged, making operating leverage visible.” |
| 48–54 s | Expand **Model logic / calculation trace** | “This trace exposes the deterministic driver relationships and highlights what the FTE change affects.” |
| 54–66 s | Scroll to commentary and human review | “Calculations come first. This demo uses disclosed offline fallback commentary, not live AI. Interpretation cannot change the numbers or approve a forecast; that remains an analyst decision.” |
| 66–75 s | Open **Variance Investigation**, select **C04**, show unresolved conclusion | “For actual performance review, evidence matters. This volume miss stays unresolved because the system cannot support a root cause.” |
| 75–85 s | On Unresolved driver, click **Request further investigation** | “The analyst requests more evidence. Deterministic calculations, bounded interpretation, and human judgment—without inventing a cause or changing the approved forecast.” |

The first minute establishes user, manual workflow pain, hybrid data boundary, dependency model and commentary limitations. If time is tight, omit a source-detail expansion; never omit the synthetic/offline disclosures or human-review boundary. Do not present an automated timing run as a spoken rehearsal or hiring-manager validation.

## Model-derived reference values

For the approved baseline with Provider FTE 4.0 → 3.5, all other assumptions unchanged:

| Output | Baseline | Scenario |
|---|---:|---:|
| Available visit capacity | 1,584 | 1,386 |
| Expected visits | 1,425.6 | 1,247.4 |
| Net patient revenue | $277,992.00 | $243,243.00 |
| Variable labor expense | $78,408.00 | $68,607.00 |
| Variable supply expense | $25,660.80 | $22,453.20 |
| Contribution margin | $173,923.20 | $152,182.80 |
| Fixed monthly expense | $85,000.00 | $85,000.00 |
| Operating income | $88,923.20 | $67,182.80 |

Operating-income impact: **−$21,740.40**. This is a regression example derived from the assumptions, never a hard-coded product output. The bridge reverses expense-delta signs: lower labor and supply expense are positive income offsets. The donut shows scenario expense of **$176,060.20**, including fixed expense. Operating margin is a presentation ratio of existing operating income to revenue; its change is percentage points, and it is N/A at zero revenue.

## Presentation and source boundaries

- One authoritative scenario engine and immutable ScenarioResult. The presentation adapter only derives bridge signs/cumulative positions, expense composition, margin ratios and dependency highlighting from this result. It never recomputes visits, revenue or income and never writes assumptions.
- Tables, KPIs, charts, trace and commentary use the same revision. Invalid drafts show the last valid results as stale and remove actionable commentary/review. Chart tooltips also identify stale data.
- SVG charts work offline and provide keyboard-focusable tooltips, exact text alternatives, roughly 260 ms geometry transitions and reduced-motion support. On narrow screens, the waterfall and detailed model table scroll inside their panels.
- Expected visits have a separate volume comparison; financial bars use a common USD scale. No fictional monthly trend or time series is shown.
- Public comparison uses already-derived consolidated labor/revenue and supplies/revenue ratios. Sources, denominator definitions and lineage remain accessible. Tenet continuing operations and different business/cost classifications limit comparability. These ratios do not numerically validate a clinic's assumptions, imply efficiency rankings, or reconcile corporate totals into clinics.
- The benchmark selector and normalized comparison cannot change scenario inputs or reviews. No HCA/Tenet affiliation, sponsorship, PHI, proprietary access, forecast accuracy or measured ROI is claimed.
- Offline fallback narrative is not live AI generation. The historical investigation narrative guard may withhold prose for additional operational targets; facts and review remain available. C01, C04, C03 and the other seven primary case narratives work.

## Reproduce validation

With test dependencies already installed:

```sh
.venv/bin/python -m unittest discover -s tests -v
python3 -m provider_fpa benchmark --directory data/synthetic_benchmark
.venv/bin/python scripts/check_presentation.py
.venv/bin/python scripts/check_browser.py
.venv/bin/python scripts/check_interpretation.py
.venv/bin/python scripts/check_investigation.py
.venv/bin/python scripts/rehearse_recruiting_demo.py
```

The rehearsal runs real browser actions on an 85-second schedule with deliberate narration pauses, blocks external requests and checks the primary outputs. It does not record speech or claim a user study. Its JSON report is written to `/tmp/provider-fpa-ticket5-rehearsal.json`; the committed acceptance copy records the actual completed run. Browser screenshots are under `/tmp/provider-fpa-ticket5-*.png`.
