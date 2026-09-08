# Provider FP&A Decision Support

This context covers recurring financial-performance review for U.S. healthcare provider organizations. It defines the language used to explain variances and prepare analyst-reviewable changes to forecast assumptions.

## Language

**Provider Organization**:
A U.S. organization that delivers patient care through one or more operating locations. The MVP serves multi-site specialty providers; hospital systems are outside its initial scope.
_Avoid_: Healthcare company, healthcare organization

**Provider FP&A Analyst**:
A finance professional responsible for recurring forecasts, budgets, variance analysis, and performance review across provider operations.
_Avoid_: Healthcare analyst, market analyst

**Performance Unit**:
A Clinic-Month, the only unit at which the MVP explains financial performance. A Market may aggregate Clinic-Month results but is not itself an explanatory unit.
_Avoid_: Hospital, market, service line

**Clinic**:
An operating location within a multi-site specialty provider at which financial and operational activity is aggregated.
_Avoid_: Facility, site, location

**Clinic-Month**:
One Clinic during one Closed Month; the intersection at which the MVP aligns financial results, operational metrics, assumptions, and events.
_Avoid_: Clinic period, monthly facility

**Calendar Month**:
A month identified uniformly as `YYYY-MM`, such as `2026-08`, across every Clinic-Month input and output.
_Avoid_: Reporting date, mixed month formats

**Market**:
A reporting group of Clinics used to aggregate results above the Clinic-Month level. It does not replace the Clinic-Month as the MVP's core analysis unit.
_Avoid_: Performance Unit

**Closed Month**:
A reporting month whose actual financial results have completed the provider's accounting close and are eligible for variance review.
_Avoid_: Current month, real-time period

**Latest Approved Forecast**:
The single forecast version authorized as the comparator for a Closed Month before variance review begins.
_Avoid_: Budget, prior year, working forecast

**Variance**:
A typed difference that must be identified as a Financial Variance, Operational Metric Variance, or Forecast Assumption Variance.
_Avoid_: Gap, anomaly, untyped variance

**Financial Variance**:
The difference between a Closed Month's actual and Latest Approved Forecast value for a financial account or metric at a Clinic-Month.
_Avoid_: Operational variance, forecast variance

**Operational Metric Variance**:
The difference between an actual and expected operating measure, such as patient visits, procedure volume, provider availability, or capacity, at a Clinic-Month.
_Avoid_: Financial variance, KPI issue

**Forecast Assumption Variance**:
The difference between the operating assumption embedded in the Latest Approved Forecast and the corresponding actual or newly supported expectation.
_Avoid_: Financial variance, assumption change

**Review Queue**:
The set of Variances selected for analyst investigation by Materiality Rules, Critical Metric Rules, or an Analyst Override.
_Avoid_: Alert list, AI-selected variances

**Materiality Rule**:
A provider-configured absolute-dollar or percentage threshold that places a Variance in the Review Queue when either threshold is exceeded.
_Avoid_: LLM materiality, fixed threshold

**Critical Metric Rule**:
A provider-configured instruction that always places specified accounts or KPIs in the Review Queue, even when their Variances do not exceed a Materiality Rule.
_Avoid_: Materiality threshold

**Analyst Override**:
An explicit analyst action that adds a Variance to the Review Queue regardless of configured thresholds.
_Avoid_: AI override, exception guess

**Operating Driver**:
An operational condition that can explain a financial result, such as patient volume, provider availability, capacity, reimbursement, payer mix, staffing, or accounting timing.
_Avoid_: Cause, factor

**Driver Family**:
One of the canonical investigation categories: Demand & Volume, Provider Availability, Clinic Capacity & Operations, Revenue Realization, Workforce & Operating Expense, Accounting & Timing, or External Disruption. Other, Unresolved, and Data Quality Issue are explicit fallback classifications.
_Avoid_: Free-form category, root cause

**Primary Driver**:
The most direct supported business mechanism explaining a Financial Variance or Operational Metric Variance.
_Avoid_: Most upstream event, most interesting story

**Contributing Driver**:
A supported upstream or secondary condition that helps explain a Primary Driver without replacing its direct business mechanism.
_Avoid_: Primary driver, background context

**Contribution Estimate**:
A quantitatively supported allocation of a Variance to a driver. It remains unknown when the available evidence cannot support an allocation.
_Avoid_: Guessed percentage, qualitative confidence

**Variance Explanation**:
An evidence-backed account of which candidate Operating Drivers plausibly produced a Variance and which remain unresolved.
_Avoid_: Summary, root cause

**Forecast Assumption**:
An explicit expectation about an Operating Driver used to produce a forecast for a Performance Unit and period.
_Avoid_: Estimate, projection input

**Assumption-Change Proposal**:
An analyst-reviewable recommendation to retain, scenario-test, or reconsider a Forecast Assumption; it is not an approved forecast change.
_Avoid_: Forecast update, automatic adjustment

**Timing Classification**:
The assessment of whether an Operating Driver is Temporary, Structural, or Unresolved over the Forecast Horizon; recurrence is a separate property.
_Avoid_: Duration

**Forecast Horizon**:
The remaining months in the Latest Approved Forecast. When no Latest Approved Forecast exists, the explicitly labeled fallback horizon is the next three Calendar Months.
_Avoid_: Fixed twelve months, implicit horizon

**Temporary Driver**:
An Operating Driver with a credible end point whose affected baseline is expected to normalize before the end of the Forecast Horizon.
_Avoid_: One-time driver, non-recurring driver

**Structural Driver**:
An Operating Driver expected to change capacity, rate, mix, demand, or cost structure through a material portion of the remaining Forecast Horizon.
_Avoid_: Permanent driver, recurring driver

**Recurring Pattern**:
A time-linked effect expected to repeat, such as seasonality. Recurrence alone does not make an Operating Driver Structural.
_Avoid_: Structural driver

**Supporting Evidence**:
A traceable input that supports or contradicts a Candidate Driver or Assumption-Change Proposal. Every evidence item retains its Source Reference.
_Avoid_: Driver, conclusion, unsupported context

**Source Reference**:
The identity and provenance of the data, document, or event record from which an Observed Fact or Supporting Evidence originates.
_Avoid_: Untraceable note, generic citation

**Observed Fact**:
A statement directly established by a traceable input or event, without a causal interpretation.
_Avoid_: Hypothesis, driver, conclusion

**Candidate Driver**:
An Operating Driver with a plausible business mechanism for a Variance but insufficient Supporting Evidence.
_Avoid_: Fact, confirmed cause

**Supported Driver**:
An Operating Driver for which Supporting Evidence and a coherent business mechanism exist, but which has not been confirmed by an analyst.
_Avoid_: Analyst-confirmed cause, proven cause

**Analyst-Confirmed Cause**:
A Supported Driver that a Provider FP&A Analyst has explicitly accepted as a cause of the reviewed Variance. AI cannot assign this status.
_Avoid_: AI-confirmed cause, supported driver

**Rejected Driver**:
A Candidate or Supported Driver contradicted by evidence or explicitly rejected by a Provider FP&A Analyst.
_Avoid_: Unresolved driver

**Unresolved Driver**:
A Candidate Driver that available evidence can neither support nor reject.
_Avoid_: Rejected driver, supported driver

**Conclusion**:
The bounded interpretation drawn from Observed Facts, Supporting Evidence, and driver states for a reviewed Variance.
_Avoid_: Evidence, driver, fact

**Clinic-Month Dataset**:
Aggregated financial and operational data aligned to a Clinic-Month, including permitted measures such as revenue, expense, volume, provider availability, staffing, capacity, closure days, and aggregate payer-mix or reimbursement metrics.
_Avoid_: Patient-level dataset, encounter dataset

**Patient-Level Data**:
Information tied to an identifiable patient, member, claim, medical record, or individual encounter. It is outside the MVP data boundary.
_Avoid_: Clinic-Month data, aggregate operations data

**Analyst Approval**:
The explicit human decision to accept, reject, or request further investigation of an Assumption-Change Proposal.
_Avoid_: AI approval, automatic approval

## Product phases

**Provider FP&A MVP**:
The first product phase, focused on explaining Closed Month actual-versus-Latest Approved Forecast Financial Variances at the Clinic-Month level and preparing Assumption-Change Proposals for Provider FP&A Analysts.
_Avoid_: Market intelligence MVP

**Market Intelligence Module**:
A possible later product phase that turns external healthcare news, filings, regulatory developments, pipeline updates, and research into cited financial briefings.
_Avoid_: Core MVP, Provider FP&A MVP
