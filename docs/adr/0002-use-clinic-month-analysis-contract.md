# Use a clinic-month analysis contract for the MVP

The Provider FP&A MVP will analyze a single Performance Unit: Clinic-Month at a multi-site specialty provider. Its standard comparison is Closed Month actual versus the Latest Approved Forecast at clinic x account or metric x month. Market is an aggregation layer only; hospital, service-line, budget, prior-year, multiple-forecast-version, and real-time comparisons remain outside the first version.

Materiality is rule-driven rather than inferred by an LLM. A Financial Variance enters the Review Queue when it exceeds a provider-configured absolute-dollar or percentage threshold, is covered by a Critical Metric Rule, or is added through an Analyst Override. The system must distinguish Financial Variance, Operational Metric Variance, and Forecast Assumption Variance rather than collapsing them into one generic variance concept.

The MVP accepts only Clinic-Month aggregated financial and operational data. It excludes patient names, dates of birth, member identifiers, claims-level protected health information, medical records, and individual encounter data. Any future use of claims or encounter-level data requires a separate decision covering governed access, minimum-necessary controls, and HIPAA-compliant handling.

## Consequences

The initial data contract and evaluation set can be substantially simpler and more comparable than a hospital-wide model, but the MVP cannot claim to explain hospital, service-line, patient-level, or real-time performance. All calculations, evidence, and explanations must preserve Clinic and Closed Month identity, and the LLM may explain queued Variances but cannot decide what is material.
