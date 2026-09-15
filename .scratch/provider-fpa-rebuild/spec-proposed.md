# Healthcare Provider FP&A Copilot — approved product and MVP specification

Status: ready-for-agent
Approval: Specification approved on 2026-09-15. Ticket drafting authorized; implementation remains on hold pending explicit user instruction.
Date: 2026-09-15
Initial MVP: Evidence-aware clinic-month variance investigation

This approved specification uses the user's supplied grill-with-docs conclusions as the source of truth, followed by compatible domain definitions and ADRs. No separate grill-with-docs transcript was found in the current checkout; discovery findings below are attributed to the user's account, not invented interview quotations or independently verified research. Earlier rebuild tickets are provisional planning artifacts, not requirements. The earlier requirements remain historical context; the five milestone tickets are regenerated for review against this approved specification. No application implementation is authorized by this document status.

## 1. Product vision

**Healthcare Provider FP&A Copilot** supports healthcare provider FP&A workflows that connect financial performance with operational context while preserving analyst judgment. Variance investigation is its first use case, not the definition or limit of the broader product.

The opportunity is to help analysts turn fragmented financial and operational information into reviewable management interpretation. The portfolio should demonstrate problem discovery, healthcare finance understanding, requirements translation, deterministic-versus-generative design, evidence boundaries, a working product, and clear business communication.

Value is a hypothesis: less manual assembly of evidence and first-draft commentary, with clearer review boundaries. Do not claim measured time savings, improved forecasting accuracy, customer adoption, or production reliability without evidence.

## 2. Initial MVP scope

**Evidence-aware clinic-month variance investigation** for a multi-site specialty Provider Organization. The narrow vertical slice is:

**Clinic-Month performance → Variance → Supporting Evidence → Operating Driver → AI commentary → human review.**

The standard financial comparison is one Closed Month's actual versus its Latest Approved Forecast. Operational measures and embedded forecast assumptions provide supporting context; they are not separate KPI or forecasting products. All demonstration data is synthetic and aggregated. Market is an aggregation concept, not a second investigation unit; no separate market dashboard is required.

Five outcome-oriented milestones organize later work: Data Intake & Validation; Variance Review Workspace; Evidence-Backed Investigation; AI Commentary + Human Review; End-to-End Demo & Validation. Driver scenarios are benchmark cases in one workflow, never separate product features.

## 3. Primary user

A **Provider FP&A Analyst**, including a healthcare provider financial analyst, preparing recurring performance reviews and explaining financial outcomes to finance and operations stakeholders.

A healthcare finance hiring manager is the portfolio audience, not a second application persona requiring separate features. The demo must make the analyst's work and the builder's reasoning understandable to that audience.

## 4. User problem

Calculating a variance is often straightforward. Understanding the operational context, checking whether an explanation is supported, and composing management-ready commentary requires more manual investigation. An incorrect P&L explanation can misdirect business decisions.

The system must help the analyst investigate and communicate, while keeping financial calculations, evidentiary judgments and final interpretation under explicit controls.

## 5. Current workflow and pain points

Based on the user's prior work and customer-discovery account, an analyst reviews financial results, identifies items needing attention, consults operational measures and event records, asks operations for missing context, reconciles competing explanations, drafts commentary, and decides whether forecast assumptions warrant review.

Relevant context includes visits, provider availability, clinic capacity and closures, staffing and overtime, reimbursement and payer mix, accounting timing, and weather. Information is fragmented across inputs and conversations. Its existence does not automatically prove causality.

Discovery shifted the original healthcare market-intelligence idea toward this recurring internal workflow. The MVP makes the evidence trail and judgment boundaries visible. It does not pretend to replace discovery conversations with operations or independently establish causal truth.

## 6. End-to-end MVP workflow

1. Open the product and understand its purpose; explicitly load the synthetic demonstration dataset.
2. Select a Clinic-Month and inspect financial performance and its comparison basis.
3. Open a Financial Variance in the rule-selected Review Queue; inspect actual, forecast, difference and direction.
4. Inspect related operational facts and source-attributed events, including missing or contradictory evidence.
5. Inspect deterministic driver family, role, evidence state, timing and unresolved questions.
6. Generate management commentary using the validated deterministic fallback; disclose that the synthetic-data demonstration is offline and does not call a live LLM.
7. Confirm or reject a supported cause, keep the investigation unresolved, or request further investigation. Assumption-Change Proposals remain advisory; separate proposal-approval and final-interpretation editing workflows are not required for this MVP.
8. Keep the decision associated with this investigation; reset the demo without changing source data.

A correctly unresolved investigation is a valid end state. No step automatically changes a forecast.

## 7. Functional requirements

| ID | Required user-visible behavior |
| --- | --- |
| FR01 | Explain the product umbrella and narrow MVP; identify synthetic data before displaying business results. |
| FR02 | Load the known five-group synthetic input contract; report validation problems with record locations. Arbitrary customer-file mapping is deferred. |
| FR03 | Maintain Clinic-Month and comparison identity throughout selection, investigation, commentary and review. |
| FR04 | Display deterministic financial differences and relevant operational/assumption differences with units, direction and unavailable-value reasons. |
| FR05 | Select Review Queue items through configured materiality/critical-metric rules; allow explicit Analyst Override and show inclusion reasons. A comprehensive rule-administration UI is unnecessary. |
| FR06 | Expose observed facts, evidence, supported and unresolved relationships, rejected candidates and source lineage in one workspace. |
| FR07 | Show Primary Driver, Contributing Drivers and upstream context distinctly; show timing and its rationale. |
| FR08 | Generate bounded commentary and disclose unavailable generation or rejected output; never silently relabel a template as AI. |
| FR09 | Support confirm cause, reject cause, keep unresolved and request further investigation in the current session; preserve the original system result and distinguish human judgment. |
| FR10 | Keep review state only in the current demo session with explicit reset; no browser storage, database, authentication or cross-session persistence. Refresh survival is not required. |
| FR11 | Demonstrate C01, C04 and C03 through the same workflow; evaluate remaining scenarios as benchmark coverage. |

### User stories

1. As a Provider FP&A Analyst, I want a clear comparison basis, so that I can trust what the variance represents.
2. As a Provider FP&A Analyst, I want input errors located in their source records, so that I can distinguish bad data from poor performance.
3. As a Provider FP&A Analyst, I want explicit actual and forecast values, so that I can check the arithmetic.
4. As a Provider FP&A Analyst, I want financial and operational variances labeled separately, so that I do not confuse measures.
5. As a Provider FP&A Analyst, I want review inclusion reasons, so that I understand prioritization.
6. As a Provider FP&A Analyst, I want to add an item for investigation, so that rule thresholds do not suppress my judgment.
7. As a Provider FP&A Analyst, I want evidence linked to its source, so that I can validate the explanation.
8. As a Provider FP&A Analyst, I want facts separated from hypotheses, so that plausible wording does not become assumed truth.
9. As a Provider FP&A Analyst, I want direct and upstream drivers distinguished, so that management hears the correct financial mechanism.
10. As a Provider FP&A Analyst, I want insufficient evidence to remain unresolved, so that the tool does not invent a root cause.
11. As a Provider FP&A Analyst, I want contradictory evidence retained, so that I can reject a tempting explanation.
12. As a Provider FP&A Analyst, I want timing tied to the forecast horizon, so that I can assess the relevance to assumptions.
13. As a Provider FP&A Analyst, I want unsupported contribution estimates left unknown, so that invented precision does not influence decisions.
14. As a Provider FP&A Analyst, I want a management-ready draft based on validated results, so that I spend less effort assembling a first draft.
15. As a Provider FP&A Analyst, I want unresolved questions and questions for operations, so that I can continue the investigation.
16. As a Provider FP&A Analyst, I want to know whether commentary came from AI or a fallback, so that I understand what the demonstration proves.
17. As a Provider FP&A Analyst, I want explicit cause confirmation and rejection, so that final causal interpretation remains human.
18. As a Provider FP&A Analyst, I want assumption proposals to remain advisory, so that reviewing an investigation cannot silently update a plan.
19. As a Provider FP&A Analyst, I want my review action distinguished from the system output, so that a draft is not mistaken for my final management interpretation.
20. As a Provider FP&A Analyst, I want review state tied to its original investigation, so that changing months cannot carry approval into another result.
21. As a portfolio presenter, I want supported, unresolved and upstream-context examples, so that I can demonstrate judgment rather than only a happy path.
22. As a healthcare finance hiring manager, I want the problem and responsibility boundaries explained within one minute, so that I can assess the candidate's business and analytical thinking.

## 8. Minimum data inputs

| Logical input | Minimum content |
| --- | --- |
| Clinic | Clinic identity/name, specialty, market reference if supplied, active dates and source. |
| Financial Value | Clinic, month, account identity/name, actual and forecast values, unit, separate currency, source and load timestamp. |
| Operational Value | Clinic, month, metric identity/name, actual and expected values, unit, source and load timestamp. |
| Operating Event | Event identity, Clinic, controlled event type, start/end dates, description, source and reported timestamp. Includes the documented synthetic forecast-horizon event. |
| Review Rule | Rule identity, account/metric applicability, absolute and percentage thresholds, critical-metric flag, effective dates and source. |

Calendar Month uses YYYY-MM. Blank effective/active end dates mean currently active where the contract permits. Validate duplicates, references, types, effective dates, source availability and units. Preserve missing numeric values as unavailable; do not substitute zero. Structural schema failures block loading, while representable missing operating facts can yield Data Quality Issue results.

Use the existing synthetic USD comparison contract and reconciled revenue/visit inputs. Label its forecast/closed-month governance as synthetic; do not invent production approval/version metadata. No individual patient, employee, provider, claim, medical-record or encounter identifiers. Real data and arbitrary upload formats are out of scope for this demo.

## 9. Structured outputs

Preserve the documented Phase 3 InvestigationResult and Phase 4 NarrativeOutput boundaries where compatible. This is a semantic contract, not a request for a new schema implementation.

| Output | Required meaning |
| --- | --- |
| Investigation identity | Clinic-Month, target and variance type, comparison basis, input snapshot identity. |
| Observed variance | Actual, comparator, signed difference, ratio or unavailable reason, unit/currency, favorable/unfavorable interpretation. |
| Review decision | Inclusion, applicable rule references or Analyst Override. |
| Investigation | Facts, evidence references, candidate/driver families, roles and states, timing/horizon/rationale, contradictions and unresolved questions. |
| Contribution | Evidence-backed amount/allocation when supported; otherwise unknown. |
| Proposal | Retain, scenario-test or reconsider/review an assumption; affected measure, rationale, supporting evidence, remaining questions and pending human status. |
| Commentary | The seven documented sections, Clinic-Month, generation mode/provider, validation outcome and human-review status. |
| Human review | Target investigation snapshot, one of the four session review actions, rationale if supplied, time and resulting review state. No separate approval editor or persistent audit identity is required. |
| Evaluation | Per-case dimension results, prohibited claims, and separate investigation/explanation success measures. Evaluation outputs are not inputs to the investigation. |

If a preserved output lacks a needed demo field, add the minimum presentation/review metadata later with a documented reason; do not redesign deterministic analysis to accommodate a page layout.

## 10. Deterministic responsibilities

Own variance arithmetic, review rules, evidence states, driver classification, timing, source lineage and structured result validity. Driver classification is evidence-constrained rule evaluation, not proof of causation and not an LLM decision.

Use actual minus comparator, preserving decimal precision; display rounding must not change review selection. Follow the existing percentage convention. Zero/missing denominator yields unavailable percentage. A revenue shortfall and expense overrun have different directional meaning even with the same arithmetic sign.

Materiality means strictly exceeding either applicable absolute or percentage threshold. Critical metrics and Analyst Override independently include an item. Unknown mechanisms remain Candidate/Unresolved. Do not key analytical answers to case IDs, Clinic IDs or gold outputs.

The exact synthetic revenue bridge and controlled operating event vocabulary remain bounded demo policies. No currency conversion, generalized causal discovery or production rounding redesign.

## 11. AI responsibilities

Approved MVP execution mode: the preserved deterministic fallback is the default narrative path, clearly disclosed with synthetic data. The guarded generative interface expresses the responsibility boundary and may remain in recovered code, but no live LLM call, API key or network access is required. Live generation is optional future scope.

Convert a validated InvestigationResult into management-ready language: explain already-supported relationships, state evidence gaps, formulate unresolved questions/questions for operations and express forecast considerations without promoting them to approved changes.

Preserve the seven Phase 4 sections: Executive Summary; Key Variances; Supported Drivers; Evidence Gaps / Unresolved Drivers; Questions for Operations; Forecast Considerations; Human Review Required.

The model cannot calculate authoritative financial values, select materiality, assign driver/timing/evidence states, invent sources, confirm causes, allocate unsupported financial impact or update assumptions. Source descriptions are data, not instructions to override these limits. Suggestions for further investigation must be questions, not newly established claims.

Retain one provider adapter, injected transport and output validation. Missing/unavailable transport can use a clearly labeled deterministic fallback. A guardrail violation must reject the model response and explain why it is not shown; preserve Phase 4's distinction between unavailable transport/schema fallback and rejected substantive content. A separately requested safe template may remain available without disguising the rejected result.

Validation checks are necessary but do not prove arbitrary prose is semantically correct. Narrative acceptance also requires reviewed benchmark examples, especially C04 refusal and C03 role separation.

## 12. Human-review responsibilities

The current-session demonstration supports exactly four required review actions: **confirm cause**, **reject cause**, **keep unresolved**, and **request further investigation**. Confirmation promotes only a Supported Driver to Analyst-Confirmed Cause; an unsupported candidate cannot become confirmed through a generic approval button. Rejection records the analyst's decision without deleting original evidence. Keep unresolved retains the evidence gap without inventing a cause or timing. Request further investigation records the need for additional evidence without confirming the explanation.

Assumption-Change Proposals remain advisory. Actual assumption changes and final management interpretation remain human responsibilities outside the automated workflow. A separate proposal approval interface or final narrative editor is not required for this recruiting MVP.

Use in-memory session-only state scoped to the investigation/input snapshot. Include reset; ending or resetting the session discards review state. Refresh survival is not required and must not be promised. Do not add localStorage, sessionStorage, a database, authentication or production state management. Switching cases or replacing input data must not transfer a prior confirmation to an unrelated investigation.

## 13. Evidence / epistemic-state rules

- Observed Fact: directly established by source data, without causal interpretation.
- Candidate Driver: plausible mechanism with insufficient evidence.
- Supported Driver: coherent mechanism and supporting evidence, not analyst confirmation.
- Analyst-Confirmed Cause: explicit human acceptance of a Supported Driver.
- Rejected Driver: contradicted by evidence or explicitly rejected by the analyst.
- Unresolved Driver: available evidence cannot support or reject it.

Every promotion or rejection must retain its basis. Facts, evidence, drivers and conclusions remain distinguishable. Missing evidence is not negative evidence; quantified alignment alone does not establish why visits fell. In C04, availability on plan rejects that specific explanation but does not establish an alternative. Unsupported roles remain unassigned.

The generative layer cannot propose state transitions. This deliberately narrows the permissive wording that AI “may propose or support a driver” in the earlier causal-boundary ADR for this MVP; no silent ADR edit is authorized.

## 14. Driver taxonomy

Use Demand & Volume; Provider Availability; Clinic Capacity & Operations; Revenue Realization; Workforce & Operating Expense; Accounting & Timing; External Disruption. Preserve Other, Unresolved and Data Quality Issue fallbacks.

Primary Driver is the most direct supported business mechanism. Contributing Drivers are supported upstream or secondary mechanisms. Upstream context is a distinct role, as in weather in C03. When competing direct mechanisms cannot be ranked, retain ambiguity rather than invent a primary driver. The taxonomy is shared across all cases; it does not imply seven pages or products.

## 15. Timing rules

Temporary requires a credible endpoint and expected normalization before the Forecast Horizon ends. Structural requires supported persistence through a material portion of that horizon. Insufficient/conflicting timing evidence remains Unresolved. Recurring Pattern is independent; seasonality is not automatically structural.

Preserve remaining approved-forecast months and the explicitly labeled next-three-month fallback when no usable horizon exists; the historical implementation also falls back for an exhausted horizon. Multiple eligible conflicting horizons fail as ambiguous. A horizon fallback never supplies missing forecast financial values.

Retain the historical 50% forecast-horizon threshold as a configurable demo heuristic. It is a demo policy, not a universal healthcare FP&A standard or a discovery-validated business rule. Preserve its existing configurable parameter; a production implementation should make it configurable for the applicable business policy. No production configuration UI is required for this MVP. Event endpoints used as recovery evidence are limited to documented mechanisms.

## 16. Source-lineage requirements

Each analytical fact/evidence item retains source identity, exact record selector, Clinic-Month or event interval, and available load/report timestamp. Derived financial values point to their contributing input records; driver and proposal claims point to supporting and contradicting evidence. The reviewer can follow references within the app without retrieving an external healthcare API.

Commentary must remain traceable to the structured investigation and its evidence. Do not label generated narrative as an original source. Distinguish retrospective snapshot analysis, which may use later loaded corroborating records, from historical as-of analysis; the latter is out of scope.

## 17. UX requirements

Show Healthcare Provider FP&A Copilot as the product name and Evidence-aware clinic-month variance investigation as the MVP description. Use a single workspace with a clear Clinic-Month selector, variance details, evidence/drivers, commentary and review. Scenario shortcuts may select data, but cannot reveal expected answers to the engine/model.

Prioritize readable financial values, plain-language evidence states, accessible controls, concise text and source inspection. Include no-data, loading, invalid-input, no-material-items, unresolved, generation-failed and review-complete states. Prevent stale commentary or review from appearing after a different Clinic-Month is selected.

In the first 60 seconds, visible copy plus narration must answer: who uses it; the manual pain; the role of operational context; the workflow; what AI can do; what it cannot do; why an analyst still decides. Explain the product through a financial work example, with technical details available only when useful.

## 18. Acceptance criteria

- AC01: A finance hiring manager can explain all seven career-demo points after a timed one-minute introduction; record actual feedback when performed, not a claim of existing validation.
- AC02: One selected Clinic-Month flows through variance, evidence, driver, commentary and explicit human review without hidden operator edits.
- AC03: Displayed C01/C04/C03 financial values match retained benchmark inputs/contracts; numeric, source and role checks pass.
- AC04: C01 supports Demand & Volume as primary and Provider Availability as contributing; it never attributes 100% of the revenue decline to PTO.
- AC05: C04 has no supported primary cause, retains unresolved timing, rejects reduced availability as an explanation, and does not invent recovery or a baseline change.
- AC06: C03 treats weather as upstream context, capacity/closure as contributing and Demand & Volume as primary; it never attributes the entire shortfall to closure without support.
- AC07: Gold answers are inaccessible to investigation and generation; evaluation remains separate.
- AC08: All authoritative arithmetic, classifications and lineage are unchanged by commentary generation or human narrative editing.
- AC09: Offline fallback output is validated and labeled; it is not advertised as live AI. Invalid causal claims do not reach the accepted commentary view.
- AC10: Confirm cause, reject cause, keep unresolved and request further investigation work in the current session; review does not alter source values or forecasts.
- AC11: Reset/session end discards review state; there is no browser-local or cross-session persistence and no cross-case stale approval. Refresh survival is not required.
- AC12: Ten-case results and narrative/browser test evidence are recorded from the actual implementation, not copied historical reports.

## 19. Benchmark / evaluation requirements

| Case | Purpose within the same workflow |
| --- | --- |
| C01 — Provider PTO | Supported primary/contributing chain and temporary timing; primary demo. |
| C02 — Provider departure | Supported persistent capacity effect. |
| C03 — Weather / clinic closure | Upstream versus direct mechanism; primary demo. |
| C04 — Unresolved Volume Miss | Refusal to fabricate causality or timing; primary demo. |
| C05 — Labor overtime | Workforce/expense mechanism. |
| C06 — Reimbursement / payer mix | Revenue realization mechanism. |
| C07 — Accounting timing | Evidence-supported accrual timing and bounded allocation. |
| C08 — Missing/invalid operating input | Data Quality Issue without invented values. |
| C09 — Seasonality | Recurrence does not imply structural change. |
| C10 — Multiple drivers | Supported roles without fabricated contribution estimates. |

Evaluate seven dimensions per case: Observed Variance, Driver Family, roles, Timing Classification, epistemic state, human-review requirement and Forbidden Conclusion. Report failures per case/dimension rather than a persuasive prose score. Unknown prohibitions or unsupported evaluator checks must not silently pass.

Successful Investigation measures correct investigation with explicit boundaries and may end unresolved. Successfully Explained Variance additionally requires analyst-confirmed supported cause and no undisclosed material unresolved issue that could change the conclusion. Before human review, autonomous explanations are not successfully explained. Historical engine completion flags must not be presented as independently verified benchmark correctness.

Ten cases are the full deterministic regression target. The three primary cases are the narrative and recruiting-demo priority. This tests adherence to designed contracts, not universal healthcare causal accuracy or real customer effectiveness.

## 20. Test strategy

Retain the previously agreed end-to-end acceptance boundary and the historical public investigation and narrative boundaries. Prefer tests of public inputs/results over internal helpers or module layout. No new generic framework is required.

- Investigation contract tests: numeric precision, zero/missing denominator, strict thresholds, critical rules, overrides, identity isolation, invalid inputs, supported/unresolved relationships, timing and lineage; run the ten-case evaluator.
- Narrative boundary tests: injected responses exercise compliant output, invented numbers/sources, role/state changes, unsupported certainty, C04 fabrication, C03 upstream confusion, missing transport and guardrail rejection. Include paraphrases rather than only exact forbidden strings.
- Human-review tests: all four session actions, supported-only confirmation, unchanged source results, reset/session isolation and stale-review prevention. No persistence or separate proposal/editor workflow is required.
- A small browser suite: C01 complete flow, C04 unresolved review, C03 causal separation, session reset and fallback-validation failure states. Test visible behavior rather than CSS structure.
- Offline default: run the entire demo and fallback tests without an API key or network-dependent model call. Historical injected model-response tests may be retained to protect the guarded boundary. Live-model smoke tests and transport setup are not MVP requirements.
- A timed presentation check validates the one-minute message and a short full demo. Narrative semantic review is explicit; regular-expression guards are not a proof of truthfulness.

The preserved historical tests are prior art available in Git, not current passing tests. Rerun after approved recovery/integration. No application tests run during this specification-only task.

## 21. Demo flow

### First 60 seconds — proposed presenter script

“Healthcare Provider FP&A Copilot helps healthcare finance analysts connect financial results with operational context. The first MVP investigates a clinic's monthly actual-versus-forecast variance. In my prior work and discovery conversations, calculating the difference was often easier than finding and validating the explanation across operating data and events. Here, deterministic logic calculates the numbers, selects review items and tracks evidence and driver states. The narrative layer is designed to turn supported results into commentary and questions. This demo uses synthetic data and an offline deterministic fallback, not a live LLM. It cannot invent causes, approve assumptions or change a forecast. The analyst reviews the evidence and owns the final interpretation. I'll show a supported explanation, an unresolved case and a weather-related case that separates upstream context from the direct financial driver.”

### Demonstration sequence

| Step | Show | Required takeaway |
| --- | --- | --- |
| C01: CL001, 2026-03 | Revenue actual $154,440 vs forecast $175,500: −$21,060 (−12%). Trace visits, availability and PTO records; show commentary and human review. | Demand & Volume is primary; Provider Availability contributes. Support is not automatic confirmation. |
| C04: CL004, 2026-06 | $196,656 vs $223,380: −$26,724 (about −11.96%). Show on-plan availability, unresolved cause/timing and a request for evidence. | Numerical alignment does not establish the operating cause. Refusal is useful behavior. |
| C03: CL003, 2026-05 | $175,875 vs $207,030: −$31,155 (about −15.05%). Follow weather → closure/capacity → visits → revenue. | Weather is upstream; capacity contributes; Demand & Volume is direct. |

These values are acceptance references for reviewers/presenters, never prompt content or hardcoded engine answers. End by distinguishing what the synthetic demo proves from future product opportunity. No unsupported ROI claim.

## 22. Explicit non-goals

Specification and ticket drafting are approved; implementation remains on hold until explicitly authorized. No production infrastructure, authentication, databases, external healthcare APIs, real PHI, RAG, real-data integration, generalized ETL, autonomous causal discovery or unnecessary model orchestration.

No standalone UI features per driver case; no detailed design of future workflows; no full forecast editor, budget tool, automatic P&L adjustment, hospital/service-line analysis, historical as-of reconstruction or complex permissions. Do not redesign existing deterministic logic without a recorded incompatibility and reason. Do not treat provisional tickets as authority over this proposal.

## 23. Future product expansion areas

Under the Healthcare Provider FP&A Copilot umbrella, possible later workflows include forecast review, budget-versus-actual analysis, management reporting, operational KPI review and external market/reimbursement context.

These are opportunities only. They carry no present implementation requirements, architecture commitments, detailed screens or automatic promise of inclusion. New discovery and scoping would determine whether to pursue each.

## 24. Definition of done

The approved MVP is done when the same runnable workflow demonstrates all three primary cases, preserves Phase 3/4 responsibility boundaries, produces traceable accepted commentary with explicit generation mode, supports the specified human decisions, and passes the recorded acceptance checks and ten-case deterministic regression suite.

A finance audience can understand the purpose and controls in a timed one-minute introduction. A short reproducible demo guide records setup, sample selection, reset, generation fallback and limitations. Portfolio claims accurately distinguish discovery insight, designed behavior, tested behavior and unvalidated business value.

An explicitly disclosed offline deterministic fallback demo fully satisfies the approved MVP narrative requirement. It must run without an API key and must not be described as live AI generation. Live LLM generation is an optional future enhancement, not an incomplete MVP acceptance item. No production deployment is required.

## Review appendix A — architecture preservation and compatibility

Current-state inspection found no application source or tests in the working tree. They were removed by commit a8a4521; historical snapshot 40e4829 includes the deterministic engine, narrative layer and old UI. Phase 4 originated in ceb51b3. Documentation and data remain, but a working current implementation cannot be asserted. This task does not restore code.

| Finding | Relationship to this proposal | Required later treatment |
| --- | --- | --- |
| Historical Phase 3 structured investigation and Phase 4 validated narrative adapter/fallback | Compatible and preferred starting point. | Recovery is approved for the later implementation stage: inspect against this specification, rerun the complete recovered test suite, retain only compatible code, and report conflicts before changing business logic. Avoid importing unwanted old UI behavior. |
| No current runnable code | Conflicts with the premise of a currently working architecture, not with its design. | Establish the approved baseline before integration; historical reports are not current evidence. |
| Earlier artifacts frame the work mainly as a variance website | Product framing is too narrow if used as the umbrella. | Use the new product/MVP distinction in eventual UI and portfolio copy. Existing artifacts stay untouched for review. |
| Earlier ADR permits AI to propose/support drivers | Broader than the new deterministic-only classification boundary. | Treat this proposal's stricter MVP rule as controlling after approval; record the reason before any later ADR change. |
| Historical narrative transport tested only through mocks | Does not establish live model generation. | Use the offline fallback by default; no live transport connection is required. Preserve compatible guarded adapter tests without adding live integration. |
| Historical numeric/keyword guards | Useful but not semantic proof. | Preserve guards and add bounded narrative acceptance cases; no wholesale finance rewrite. |
| Earlier provisional ticket proposes fallback on guardrail failure | Risks obscuring rejected substantive content; differs from Phase 4's documented behavior. | Preserve explicit rejection and label any separately chosen safe template. |
| Historical generator uses >= while engine policy uses > | Inconsistent exact-threshold behavior; existing ten cases do not expose equality. | Keep strict > contract; add boundary verification and fix only if recovered behavior requires it. |
| Historical 50% timing policy; exact USD bridge; controlled event vocabulary | Compatible bounded demo policies, not general finance standards. | Preserve and disclose limits; the configurable 50% demo heuristic is now approved. |
| Historical human-review helper lacks the required session UI flow | Gap for full demo and final interpretation, not reason to replace analysis. | Add only the four approved session review actions during later implementation; no persistence. |
| Legacy fixture approval/version metadata is limited | Insufficient for real-data ingestion; adequate only as disclosed synthetic setup. | Keep real integration deferred rather than fabricate production governance. |

## Review appendix B — approved decisions and implementation gate

All four product decisions were resolved by the user on 2026-09-15:

1. Selectively recover historical Phase 3/4 engine, guarded narrative layer and compatible tests rather than rebuild. After recovery, inspect against the approved specification, rerun the complete test suite and report conflicts before changing business logic. Recovery itself begins only when implementation is explicitly authorized.
2. Default to the disclosed offline deterministic fallback with synthetic benchmark data. No live API key dependency. Live LLM generation is optional future scope and not required for MVP completion.
3. Use session-only review: confirm cause, reject cause, keep unresolved, request further investigation. No database, authentication, browser-local persistence or production state management.
4. Retain the historical configurable 50% forecast-horizon threshold as a demo heuristic, not a universal healthcare FP&A standard. Production use should allow business-specific configuration.

No unresolved product decision blocks drafting the five tickets. Code-specific compatibility findings must be reported after recovery and before any business-logic change. The original grill-with-docs transcript was not found; supplied conclusions govern. The previously approved highest-level acceptance boundary and historical public investigation/narrative contracts remain preferred.

## Review appendix C — approved input to to-tickets

Use this approved specification, the resolved decisions, compatibility findings and acceptance IDs to regenerate the five provisional milestones for user review. Their content must reflect the offline default and session-only review. Ticket generation is authorized; ticket execution is not.

1. **Data Intake & Validation:** selectively recover and verify the compatible Phase 3/4 baseline before exposing known synthetic input loading and validation. Record recovery conflicts before changing business logic. Own FR01–FR03 foundations.
2. **Variance Review Workspace:** expose Clinic-Month actual-versus-forecast performance, typed variances, queue reasons and Analyst Override. Own FR03–FR05.
3. **Evidence-Backed Investigation:** expose source lineage, states, driver roles and configurable demo timing in one workflow. Prioritize C01, C04, C03; remaining scenarios are benchmark coverage. Own FR06–FR07.
4. **AI Commentary + Human Review:** expose guarded offline fallback commentary and the four session-only review actions. No live integration or persistence task. Own FR08–FR10.
5. **End-to-End Demo & Validation:** run the complete suite and ten-case evaluation, verify the three primary demo scenarios and one-minute explanation, and record honest portfolio evidence. Own FR11 and overall AC01–AC12/definition of done.

Each milestone delivers observable behavior and its tests. Do not create a sixth driver feature, real-data milestone or production-foundation task. Earlier ticket assumptions about live AI and persistent state are superseded. The user will review regenerated tickets before authorizing implementation.

## Reference basis

Repository domain glossary, four retained ADRs, Phase 3 investigation documentation, Phase 4 narrative documentation, retained Synthetic Benchmark inputs/expected contracts, and inspected historical narrative source. Source precedence is the user's latest supplied discovery conclusions and explicit scope.

The selected approach follows simple controlled workflows rather than unnecessary agent complexity ([Anthropic, Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)); browser checks focus on user-visible behavior ([Playwright Best Practices](https://playwright.dev/docs/best-practices)). These references inform engineering practice, not healthcare discovery claims.
