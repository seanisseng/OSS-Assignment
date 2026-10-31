# Historical hosted Action run history

This is a historical record of earlier smoke and version 2/3 attempt failures.
The version 3 capture is finished: 19 hosted attempts produced eight valid
outputs, eight contract failures and three HTTP 429 failures; three attacks were
never dispatched, and the separate six-case recovery is reported apart. See
[the experiment review](EXPERIMENT-REVIEW.md) and
[final review](reviews/FINAL-22-CASE-REVIEW.md). The earlier seven-case
development batch (1/5 real, 2/2 diagnostic) is a different configuration,
preserved in `evals/evidence/development-batch-20261030/`. Older "pending"
statements below describe their dated attempts; they are not current claims.
Every failure remains preserved.

# Hosted GitHub Action run history

Repository: seanisseng/OSS-Assignment. These are manually dispatched, artifact-only
smokes of development case `pytest-15051` on 29 October UTC (29?30 October Singapore).
Seven failed; the eighth passed the complete technical workflow. Model decision
quality, human assessments and the full evaluation remain unfinished. Publication
was disabled throughout; no sandbox issue comment was posted.

## Attempts and observed outcomes

| Run | Failure | Reported usage | What the run established |
|---|---|---|---|
| [40821878074](https://github.com/seanisseng/OSS-Assignment/actions/runs/40821878074) | The pinned launcher resolved `auto` to `claude-sonnet-5.5`; the provider rejected that model with HTTP 400. | Zero reported inference usage. | Trusted setup ran, but the assessment never reached inference. |
| [40823996951](https://github.com/seanisseng/OSS-Assignment/actions/runs/40823996951) | Clearing the model selector avoided alias substitution, but the proxy-backed BYOK path required an explicit model. | Zero reported inference usage. | An empty model selector is incompatible with this provider path. |
| [40827503414](https://github.com/seanisseng/OSS-Assignment/actions/runs/40827503414) | Native Auto worked, but repeated large-input reads and helper delegation ended with upstream HTTP 429. No `output/recommendation.json` was written, so artifact preservation failed and validation was skipped. | Analysis 10.08027 credits; detection 0.28257; total 10.36284. Actual account billing is unconfirmed. | Provider responses occurred and the canonical skill content was read. Model-selection compatibility was fixed; task completion was not. |
| [40889513595](https://github.com/seanisseng/OSS-Assignment/actions/runs/40889513595) | The approved report-first export loaded and no delegation occurred, but the agent ignored the two-chunk instruction and read one chunk 26 times. HTTP 429 ended execution with no recommendation; validation was skipped. | Analysis 16.76448 credits; detection 0.43191; total 17.19639. Actual billing is unconfirmed. | Smaller input and CLI exclusions did not prevent a read loop. The runtime recorded 46 turns despite the configured 16-turn value. Detection also hit HTTP 429. |
| [40900450929](https://github.com/seanisseng/OSS-Assignment/actions/runs/40900450929) | One request was rejected for an empty tools list combined with tool_choice (HTTP 400, invalid_request_body). No recommendation; validation skipped. | No successful inference usage records; token log empty. Actual billing unconfirmed. | One-request termination and capture worked. The format correction is local and tested; no retry dispatched. See docs/SINGLE-RESPONSE-AUDIT.md. |
| [40917225932](https://github.com/seanisseng/OSS-Assignment/actions/runs/40917225932) | Inference returned and saved a recommendation, then a direct protected marker write failed EROFS. The response also had object-shaped evidence; validation skipped. | 2,706 reported tokens; actual billing unconfirmed. | Request compatibility and response capture worked; output/finalization did not. |
| [40920259777](https://github.com/seanisseng/OSS-Assignment/actions/runs/40920259777) | Agent and clean JSON validation passed. Conclusion failed because removing the marker caused missing_terminal_safe_output. | 2,199 reported tokens; proxy estimate 0.042885 credits, actual deduction unconfirmed. | Required terminal noop was omitted. Fixed CLI completion passes local pinned bridge/collector/conclusion replay; hosted proof and human semantic review pending. |
| [40924362394](https://github.com/seanisseng/OSS-Assignment/actions/runs/40924362394) | All five jobs passed, including clean JSON validation and final conclusion. One inference request and one fixed trusted noop. | 2,278 reported tokens; proxy estimate 0.047625 credits, actual deduction unconfirmed. | First successful hosted technical smoke. Recommendation still needs human quality review; no publication. |

## Model selection

The sixth hosted attempt, [40917225932](https://github.com/seanisseng/OSS-Assignment/actions/runs/40917225932),
made one successful request and saved a recommendation. Its response identified
`gpt-4o-mini-2024-07-18` and reported 2,706 tokens. The harness then failed with
`EROFS` writing a framework marker on a read-only mount. Clean validation was
skipped; offline validation also rejects its object-shaped `evidence` field.
Actual billing remains unconfirmed. The [output-failure audit](SINGLE-RESPONSE-AUDIT.md#second-smoke-response-capture-and-output-contract)
records the local fixes and regression proof; another hosted run needs approval.

The pinned gh-aw v0.93.5 launcher supported preserving native Auto, but did not
pass the relevant option at its main model-resolution site. The correction in
`scripts/compile_workflows.py` inserts that option only after checking the exact
launcher SHA256 and expected source shape. Unknown launcher bytes fail closed.
Both analysis and detection receive the compatibility correction. The third
run logged `configured=auto resolved=auto`; response usage identified
`gpt-4o-mini-2024-07-18`. Auto remains unpinned and may choose a different model.
See [the compatibility record](STUDENT-AUTO.md).

## Input handling and excessive investigation

The original hosted export bundled the report and approved historical source
into one approximately 204 KB JSON line. The report body itself was 1,220
characters. The file-reading tool rejected reading the entire large file.
The agent tried to invoke the skill as an agent, then spawned a general-purpose
helper. The helper repeatedly searched and read the same content and attempted
paths absent from the isolated workspace. This consumed requests without
producing the required structured decision.

The parent session's eight-turn setting did not bound the delegated helper's
additional turns. A prompt to use a skill did not prevent delegation, and the
workflow's tool declarations did not remove those native tools. This motivates
explicit native tool exclusions and a report-first export rather than a larger
budget. It also shows why the canonical skill must be read and applied directly.

## Rate limits, credit settings and misleading success signals

The third trace records an upstream `429 Too Many Requests` response with a
retry interval of roughly 47 minutes. The observed terminal error was GitHub's
rate limit, not an explicit proxy credit-limit rejection. Raising the credit
budget would not address repeated reading or helper delegation.

At that time the configured budgets were ten analysis credits, five detection
credits and fifteen daily per workflow. Analysis usage slightly exceeded ten:
completed-response accounting means the configured value is not an exact billing
ceiling. A failed workflow can consume credits when inference has already begun.
Zero usage applies to the first two startup failures, not to the third attempt.

The third detector also encountered rate limiting. Its job appeared successful
because the framework tolerates an execution error; this is not evidence of a
completed threat scan. Likewise, a successful model execution step is not proof
that the output file exists, validates, or contains a correct case decision.

## Current response and remaining verification

The smoke switch was reset to false after preparation of the fourth attempt; publication remains
disabled. Original GitHub runs and logs remain the evidence source. Temporary
downloaded debug copies were removed after inspection. Local summaries are in
`evals/evidence/native-auto-verification.json` and `execution.json`.

The [simplified configuration](SIMPLIFIED-WORKFLOW.md) keeps the report separate
from lossless optional context chunks, removes native delegation tools from
analysis, and bounds configured usage. It was pushed as `eb46064` after explicit
approval and tested once in run 40889513595. Its reading instruction and configured
turn value did not constrain the observed loop. A further configuration change
requires renewed human approval; no additional inference is authorized.

Any next hosted run needs enforceable read/turn bounds, output creation and
validation, decision quality and usage checks; raising limits alone did not work.
All failures must remain in the experiment record. The assignment also permits
the documented coding-assistant dry-run route; further hosted spending is optional.

## Documentation check: credits and rate limits

GitHub distinguishes the monthly AI-credit allowance from temporary request-rate
limits. Having remaining credits does not establish that requests will be admitted.
See [Copilot usage limits](https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/usage-limits).
The repeated large-input requests plausibly contributed to the third failure,
but the trace does not establish the precise rate-limit threshold or prove that
file size alone caused the rejection.

Credits depend on model and input, output and cached tokens; one case is not one
credit or one model call. The third analysis recorded 32 successful responses,
301,666 input tokens, 728,704 cached-read tokens and 1,500 output tokens. At the
documented conversion, 10.36284 credits represents about USD 0.104 of usage value,
not proof of an additional charge. See [individual billing](https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/billing).
Copilot Student uses native Auto; see [supported models](https://docs.github.com/en/copilot/reference/ai-models/supported-models).

Correction: the daily credit setting does not protect these manual smoke runs.
Both the [gh-aw cost documentation](https://github.github.com/gh-aw/reference/cost-management/)
and the [exact pinned guardrail source](https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/check_daily_aic_workflow_guardrail.cjs)
explicitly bypass the daily check for workflow_dispatch. Per-run proxy limits,
timeouts, the smoke switch and the explicit dispatch-count guard remain separate
controls. Do not describe a daily frontmatter value as an enforced manual budget.

The native [Copilot CLI session-limit option](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/set-session-limit)
currently requires at least 30 credits. This repository instead sets gh-aw
frontmatter limits compiled into the firewall API proxy; the native CLI minimum
does not establish that the workflow's smaller proxy settings are invalid.

## Account display versus proxy accounting

After the fourth run, the user supplied a screenshot of their October 2026
Copilot Student AI usage page showing 3 of 200 included credits used. It does
not show the roughly 17.20-credit deduction that the fourth proxy total might
suggest. The inspected response record explicitly sets
`ai_credits_pricing_source` to `models.dev`, with `concrete_model` accounting.
These values are token-based workflow cost calculations, not a GitHub account
ledger. Actual charged or deducted credits remain unknown. The difference is
not proof of free usage, nor evidence that billing must update after a particular
delay. See [GitHub usage monitoring](https://docs.github.com/en/copilot/how-tos/manage-and-track-spending/monitor-ai-usage)
and the [gh-aw accounting formula](https://github.github.com/gh-aw/specs/ai-credits-specification/).

## Proposed response to the fourth failure

The [single-response revision](SINGLE-RESPONSE-REVISION.md) moves context selection
into trusted preparation and removes investigation tools from the assessment
model. One response is validated by Python, without automatic repair calls.
This is now implemented and tested with mocked responses in a separate workflow,
not a successful hosted fix. Actual adapter compatibility, semantic skill use and
excerpt quality remain to be evaluated before claiming end-to-end success.

## Third single-response smoke: completion protocol

The [completion audit](SINGLE-RESPONSE-AUDIT.md#third-smoke-required-terminal-output)
records the seventh run, the incorrect assumption behind removing the marker,
the trusted CLI correction and offline replay evidence. It supersedes earlier
claims that no terminal safe output was needed. A successful inference or valid
recommendation artifact is insufficient for the framework's final conclusion.
