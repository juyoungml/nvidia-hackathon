# Frozen v2 trajectory audit

This offline audit applies the same heuristics to D and G. Flags are review prompts, not accuracy scores. Display withholding is reported separately from content. No winner aggregate is computed.

## Arm D (5 traces)

- **selection_overflow**: 3/5 traces; 3 events. Example: `evaluation/system2-results/v2/domain-13.json#/validation/reason`
- **output_withheld**: 3/5 traces; 3 events. Example: `evaluation/system2-results/v2/domain-13.json#/display/status`
- **direction_needs_endpoints**: 1/5 traces; 2 events. Example: `evaluation/system2-results/v2/domain-3.json#/validation/selection/next_checks/0/rationale`
- **numeric_rationale_review**: 2/5 traces; 2 events. Example: `evaluation/system2-results/v2/domain-3.json#/validation/selection/next_checks/2/rationale`
- **causality_review**: 1/5 traces; 1 events. Example: `evaluation/system2-results/v2/domain-3.json#/validation/selection/next_checks/1/rationale`

## Arm G (5 traces)

- **direction_needs_endpoints**: 1/5 traces; 1 events. Example: `evaluation/system2-results/v2/general-63.json#/validation/selection/next_checks/1/rationale`
- **numeric_rationale_review**: 4/5 traces; 4 events. Example: `evaluation/system2-results/v2/general-13.json#/validation/selection/next_checks/0/rationale`

## Interpretation

Prioritize output bound control, then review linked trend and numeric rationales. A selected ID establishes a reference link, not that the prose follows from it. Causality flags require human reading. Raw selections from withheld v2 traces were parsed for audit only; they remain withheld under the original contract.
