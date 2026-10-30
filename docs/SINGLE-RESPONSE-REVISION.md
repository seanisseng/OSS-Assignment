# Single-response revision: hosted completion verified

The user approved configuration `3e538ec9...`, pushed as `c5cd1cd`, and one smoke.
Run 40900450929 made one request and failed with HTTP 400 before producing an
assessment. The [audit and correction](SINGLE-RESPONSE-AUDIT.md) record the exact
request error, local regression fix and remaining compatibility checks. The fix
was approved as configuration `3115d8ad...` for a push and one follow-up smoke.
That second request exposed a protected marker write and malformed output. The
approved third request passed inference and clean JSON validation, then failed
the required terminal-output check. Configuration 6b9412c7 was approved and
passed all jobs in run 40924362394; all seven prior failures remain in GitHub.

## Evidence motivating the change

In [run 40889513595](https://github.com/seanisseng/OSS-Assignment/actions/runs/40889513595),
the report-first export loaded and no delegation was observed. Nevertheless, the
agent read one context chunk 26 times and recorded 46 turns despite a configured
value of sixteen. It ended with HTTP 429 and no recommendation. Splitting files,
prompt instructions and a higher budget did not enforce a bounded assessment.
See [the hosted failure record](HOSTED-ACTION-ISSUES.md).

The proxy calculated 17.19639 credits using model-price accounting; this is not
verified consumption of the student's included allowance. The user's account
screenshot showed 3 of 200 credits used. No billing delay or free-use explanation
has been established. Request-rate restrictions are separate from that allowance.

## Implemented workflow

1. Trusted preparation checks the case, configuration approval and attempt guard.
   It builds one size-bounded assessment packet containing the complete issue,
   the canonical skill text and relevant historical source excerpts. Original
   snapshots remain unchanged and available to humans for audit.
2. `scripts/single_response.py` selects only explicit report file/line references
   that resolve to an approved source key: up to four 21-line excerpts, centered
   on the cited line. It records evidence keys, ranges, source/excerpt hashes and
   files not excerpted. Non-source context, including simulated tool responses,
   is preserved as untrusted evidence. Selection does not read expected decisions.
3. `scripts/single_response_harness.cjs` sends the packet directly in one gateway POST.
   The assessment model receives no file-reading, search, shell, network,
   delegation or publication tools. Skill use means applying the supplied skill;
   it must not require a separate skill or helper-agent invocation.
4. Accept one structured recommendation using the existing decision contract.
   If supplied evidence leaves uncertainty, the model may return `human_review`.
   A missing or invalid response remains a failed attempt, not a fabricated
   abstention. Do not service tool requests or make repair/retry model calls.
5. Trusted Python validates case/hash binding, evidence keys, fields, decision,
   questions and size limits. Save the exact raw response and validation result.
   Publication remains a separate human-reviewed operation by the existing
   restricted publisher; this revision initially produces artifacts only.

## Enforcement and compatibility boundary

The custom harness is supported by the pinned gh-aw compiler. It calls the AWF
Copilot Chat Completions gateway with `model: auto` and `n: 1`. The local correction
omits tools and tool_choice entirely; it offers no model tools, follows no
redirects and has no retry loop. It does not launch a
Copilot CLI agent session or resolve Auto into a chosen concrete model. The
fixed local endpoint is `http://api-proxy:10002/chat/completions`; credentials
remain in AWF's proxy. This is an integration with the documented proxy, not a
claim that Copilot exposes a public direct-inference REST API.

The caller aborts after at most 540 seconds, reduced by elapsed AWF startup time,
inside the ten-minute execution step. This leaves a minute for evidence cleanup.
Cancellation, runner loss or an external hard kill can still interrupt finalization;
a request_sent trace without a terminal event is incomplete, never successful.
The caller requests at most 2,048 output tokens, bounds
the packet to 32 KiB and provider response to 64 KiB, and accepts at most 32 KiB
of recommendation text. One fixed gateway request is enforced in caller code,
not by the previously ineffective turn setting. If the complete issue exceeds
the packet allowance, fail
preparation for human handling instead of silently truncating the report.

The local correction has a five-credit proxy setting, a declared daily setting
of fifteen, and no separate AI detector. This supersedes the deployed twenty-credit
setting; actual one-request cost has not been measured and is not assumed to be one credit.
It has no model-selectable external action and emits only a fixed trusted framework noop;
the recommendation is only a raw artifact until clean Python
validation. An AI threat verdict is unnecessary for that restricted artifact
path and cannot replace structural validation. The publisher rejects this
workflow's identity. Legacy workflows retain their separate detector.

The harness prompt includes a closed JSON Schema with field types, decisions,
missing-information categories and allowed evidence identifiers. In particular,
`evidence` must be a nonempty array of source-key strings, never copied objects.
This schema is supplied as instructions, not an unverified provider API option.
Python remains authoritative: invalid output is retained and rejected without
coercion, automatic retries or repair calls. The harness writes only workspace
artifacts without directly writing the read-only framework safe-output path.
After capture, trusted code calls the installed safeoutputs CLI with a fixed noop;
the model cannot control this command or its arguments. A terminal completion
acknowledgement is required in the trace and by clean Python validation. The CLI
has a 15-second timeout, 16 KiB output bound and no retries. See the
[third-smoke correction](SINGLE-RESPONSE-AUDIT.md#third-smoke-required-terminal-output).

Preparation requires the new `CLARIFICATION_SINGLE_RESPONSE_ENABLED=true` switch,
main in the allowlisted repository, an allowlisted development case and a current
signed configuration. The seven-case menu covers five real development inputs
and diagnostic-crash/diagnostic-trigger; held-out cases are rejected. Clean
validation also binds the artifact to the selected case.
At the user's explicit request, there is no lifetime dispatch-count limit or
manual-rerun prohibition. Each manual dispatch or rerun can make one request;
there are no automatic retries. Repeated tests of unchanged approved code do
not require a counter reset or new configuration hash. External push/run approval
is still required. The daily setting does not constrain manual dispatch. Reset
the switch after preparation; cancel running jobs to stop them. Preserve all history.

Preparation first creates `output/preparation.json`, then records prepared or
refused status and re-raises the original error. The always-run raw upload warns
if no files exist; the validated-artifact upload still errors on a missing result.
The execution step retains GitHub's default success condition, so failed preparation
skips it instead of trying to load an uninstalled harness.

The compiler retains a CLI step label and shell/write/all-paths arguments. These
arguments are unused: the replacement harness ignores argv and never starts the
Copilot CLI. Trusted finalization calls only the fixed safeoutputs CLI. Model tool
availability is determined by the request, which offers no tools.

`request.json` captures the actual skill text and packet delivered to the model.
`execution.json` records the sole request and packet/skill hashes; raw responses,
including malformed JSON, are retained for inspection. A clean validation job
reconstructs the packet from frozen source, checks the captured request, then
validates the recommendation against the original case. This is delivery
evidence, not proof of semantic skill compliance; human review remains required.
The legacy dry-run filesystem-trace validator is unchanged and must not be used
to claim the new hosted request evidence is a filesystem-read event.

## Validation and trade-offs

Local tests cover oversized packets/responses, tool requests, multiple responses,
malformed JSON, rate errors and timeout abortion without repair calls. A mocked
preparation/request/clean-validation integration checks complete reports, excerpt
provenance, the captured skill and stale/multiple-request rejection. Publisher
tests reject the new workflow. All 22 frozen inputs fit without truncating reports.

Limited excerpts may omit useful evidence and increase human-review decisions.
The proposal prevents model-driven file-reading loops by removing their tools;
it cannot guarantee correct decisions or prevent provider rate limiting.
Evaluate actual outputs in fresh sessions against the frozen historical and
adversarial expectations, and obtain student semantic assessments.
Only after local checks and separate approval should one hosted smoke test verify
request count, skill evidence, output creation/validation and reported usage.

The first run failed gateway request validation. The second returned a response
from gpt-4o-mini-2024-07-18, then failed a read-only framework marker write; its
evidence field also violated the contract. The third passed JSON validation but
failed its final conclusion for missing terminal safe output. Billing remains unverified. The one-request claim is
about the caller's gateway POST; inspect proxy logs for any upstream behavior.
Local verification is recorded in `evals/evidence/single-response-verification.json`.

Verification: 69 Python tests pass, including eighteen Node transport/harness cases.
The Node harness has approximately 98% line and over 80% branch coverage. Timeout-finalization,
refusal receipts and artifact ZIP extraction are covered. Compilation uses gh-aw v0.93.5.
The initial missing adapter and missing case-identity guard were reproduced as
failing tests before implementation/fix. These results use mocked transport only.

References: [custom harnesses](https://github.github.com/gh-aw/reference/engines/),
[AWF proxy](https://github.com/github/gh-aw-firewall/blob/v0.28.70/docs/api-proxy-sidecar.md),
[dynamic Auto accounting](https://github.com/github/gh-aw-firewall/blob/v0.28.70/docs/awf-config-spec.md).
