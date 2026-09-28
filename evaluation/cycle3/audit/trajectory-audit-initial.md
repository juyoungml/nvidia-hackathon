# Frozen v2 trajectory audit — initial stage

This offline audit applies the same heuristics to D and G. Flags are review prompts, not accuracy scores. Display withholding is reported separately from content. No winner aggregate is computed.

## Arm D (7 traces)

- **selection_overflow**: 5/7 traces; 5 events. Example: `evaluation/cycle3/traces/domain-3.json#/validation_attempts/0/reason`
- **output_withheld**: 5/7 traces; 5 events. Example: `evaluation/cycle3/traces/domain-3.json#/validation_attempts/0/status`
- **direction_needs_endpoints**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/domain-13.json#/validation_attempts/0/selection/next_checks/1/rationale`
- **numeric_rationale_review**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/domain-60.json#/validation_attempts/0/selection/next_checks/0/rationale`
- **causality_review**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/domain-13.json#/validation_attempts/0/selection/next_checks/1/rationale`

## Arm G (7 traces)

- **output_withheld**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/general-63.json#/validation_attempts/0/status`
- **schema_invalid**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/general-63.json#/validation_attempts/0/reason`
- **numeric_rationale_review**: 3/7 traces; 3 events. Example: `evaluation/cycle3/traces/general-13.json#/validation_attempts/0/selection/next_checks/1/rationale`
- **repeated_identical_tool_call**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/general-63.json#/tool_calls/6`

## Interpretation

Prioritize output bound control, then review linked trend and numeric rationales. A selected ID establishes a reference link, not that the prose follows from it. Causality flags require human reading. Initial display status is inferred from the first validation attempt; no initial display was saved. Content flags are assessed only for accepted selections in stage-aware traces.
