# Preserve causal and evidence boundaries in variance investigations

The MVP will use five logical input groups: Clinic, Financial Value, Operational Value, Operating Event, and Review Rule. Person-level employee, provider, patient, claim, medical-record, and encounter identifiers remain outside the contract; provider availability is represented through Clinic-Month aggregates. Open-ended `active_to` and `effective_to` values mean currently active, every month uses `YYYY-MM`, financial unit and currency are separate, and every analysis-relevant input retains a Source Reference.

Variance investigations use seven Driver Families: Demand & Volume, Provider Availability, Clinic Capacity & Operations, Revenue Realization, Workforce & Operating Expense, Accounting & Timing, and External Disruption, plus explicit Other, Unresolved, and Data Quality Issue fallbacks. A Variance may have multiple drivers, but its Primary Driver is the most direct supported business mechanism; upstream causes are Contributing Drivers. Contribution Estimates are recorded only when quantitatively supportable.

The Forecast Horizon is the remaining period in the Latest Approved Forecast, falling back to the next three Calendar Months when no approved forecast exists. Temporary and Structural describe expected persistence over that horizon; Recurring Pattern is independent and does not imply Structural.

The investigation must keep Observed Fact, Supporting Evidence, Operating Driver, and Conclusion distinct. A driver moves through Candidate, Supported, and Analyst-Confirmed states, or becomes Rejected or Unresolved. AI may propose or support a driver but can never assign Analyst-Confirmed Cause.

## Consequences

The product must preserve provenance and epistemic state in both its data model and user interface. A plausible narrative is not a successful explanation, upstream events cannot skip the direct business mechanism, missing evidence cannot be presented as negative evidence, and the analyst remains the sole authority for confirming a cause.
