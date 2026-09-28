# Frozen v2 trajectory audit — final stage

This offline audit applies the same heuristics to D and G. Flags are review prompts, not accuracy scores. Display withholding is reported separately from content. No winner aggregate is computed.

## Arm D (7 traces)

- **output_withheld**: 4/7 traces; 4 events. Example: `evaluation/cycle3/traces/domain-3.json#/display/status`
- **reference_invalid**: 4/7 traces; 4 events. Example: `evaluation/cycle3/traces/domain-3.json#/validation/reason`
- **supporting_ref_known_but_unselected**: 4/7 traces; 7 events. Example: `evaluation/cycle3/traces/domain-3.json#/validation_attempts/1/raw_output`
- **direction_needs_endpoints**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/domain-13.json#/validation/selection/next_checks/1/rationale`
- **numeric_rationale_review**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/domain-60.json#/validation/selection/next_checks/0/rationale`
- **causality_review**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/domain-13.json#/validation/selection/next_checks/1/rationale`

## Arm G (7 traces)

- **direction_needs_endpoints**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/general-63.json#/validation/selection/next_checks/1/rationale`
- **numeric_rationale_review**: 3/7 traces; 3 events. Example: `evaluation/cycle3/traces/general-13.json#/validation/selection/next_checks/1/rationale`
- **repeated_identical_tool_call**: 1/7 traces; 1 events. Example: `evaluation/cycle3/traces/general-63.json#/tool_calls/6`

## Interpretation

Prioritize output bound control, then review linked trend and numeric rationales. A selected ID establishes a reference link, not that the prose follows from it. Causality flags require human reading. Content flags in stage-aware traces assess the final displayed selection.
