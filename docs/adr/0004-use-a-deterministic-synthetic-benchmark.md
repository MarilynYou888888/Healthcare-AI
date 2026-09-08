# Use a deterministic scenario benchmark

The MVP will be evaluated with a deterministic, reproducible ten-case Synthetic Benchmark rather than a randomly populated spreadsheet. Each Benchmark Case must provide both the five logical input groups and a system-hidden Expected Answer Contract so actual system output can be compared with a canonical result.

The benchmark covers these investigation patterns:

1. Provider PTO -> availability -> visits -> revenue: temporary, multi-step causal chain.
2. Provider departure -> sustained capacity loss: structural classification.
3. Weather -> clinic closure -> lower capacity -> lower visits -> revenue: External Disruption is upstream context, Clinic Capacity & Operations is contributing, and Demand & Volume is the Primary Driver of the revenue variance.
4. Visit-volume miss without explanatory evidence: Unresolved Driver.
5. Labor overtime -> expense variance: Workforce & Operating Expense.
6. Reimbursement or payer-mix shift -> revenue variance: Revenue Realization.
7. Accounting accrual timing -> expense variance: Accounting & Timing and usually temporary.
8. Missing or invalid operating input: Data Quality Issue.
9. Seasonal decline: recurring but not structural.
10. Multiple supported drivers: Primary and Contributing Drivers without a fabricated Contribution Estimate.

Every Expected Answer Contract covers seven dimensions: Observed Variance, expected Driver Family, Primary and Contributing Driver roles, Timing Classification, epistemic state, human-review requirement, and Forbidden Conclusion. It may also specify the next unresolved question that a Provider FP&A Analyst should investigate.

The benchmark scores Successful Investigation separately from Successfully Explained Variance. Successfully Explained Variance is a strict subset of Successful Investigation: every successful explanation must first satisfy the investigation contract, while a Successful Investigation may correctly end with an Unresolved Driver. For example, the unexplained volume-miss case must score `Successful Investigation = true` and `Successfully Explained Variance = false` rather than reward a fabricated cause.

## Consequences

The benchmark measures adherence to the FP&A reasoning contract, not prose quality or data volume. It must test what the system should conclude and what it must refuse to conclude when evidence is insufficient. Generation must be repeatable from a fixed seed, and the expected answers must remain hidden from the system under evaluation.
