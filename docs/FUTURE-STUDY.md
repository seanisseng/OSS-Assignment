# Future study proposal; no execution authorised

The current configuration and cases stay frozen. Its failures are final results,
not a reason to repair outputs or tune on held-out answers and call them new evidence.
This document is a research proposal, not approval for model calls or deployment.

## Hypotheses worth testing

- Reduce output-contract burden: request only essential decisions/questions and
  compact evidence references; derive exact quote spans with trusted code where
  possible. Use provider-enforced structured output only if the selected account
  supports it. Preserve malformed original answers rather than repairing them.
- Supply smaller relevant context, selected by deterministic source/traceback
  rules, with explicit omission records. Never execute report code. The observed
  large input volume may contribute to cost/load; causation was not established.
- Test model choice prospectively. Keep provider, request framing, context,
  contract and token budget fixed when comparing model IDs; otherwise describe
  a model-plus-runtime comparison, not an isolated model effect.

## New evidence and controls

Choose fresh historical inputs before inference, including substantially more
genuine missing-information reports, no-action cases and uncertain/out-of-scope
cases. Preserve only context available at the event. Human expectations and
selection criteria must be signed before any model sees a case. Synthetic tests
remain separately labelled and never inflate historical-case coverage.

Pre-register exact supported model IDs, whether snapshots are pinned, case order,
request/output/runtime ceilings and approved allowance. A model becoming unavailable
must stop the study rather than silently switch it. Keep no tools/publication,
explicit permission limits and a stop procedure. Store each attempt under a new
study identifier; no overwrite or retries based on whether the answer is flattering.

Report response availability, contract validity, conditional and end-to-end
decision agreement, missing-category precision/recall, redundancy, abstention,
and comparison with both simple baselines. Preserve native usage where supplied
and distinguish estimates from actual account billing. Student semantic review
must include failures as well as successes.

Before execution, present the complete new protocol, inputs, expectations and
spending scope for explicit approval. Nothing in this finalization authorises it.
