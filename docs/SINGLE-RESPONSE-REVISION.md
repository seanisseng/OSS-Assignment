# Single-response revision: approved for one hosted smoke test

The user requested implementation and local testing before another hosted run.
The replacement is a separate `single-response.md` workflow and compiled lock.
The original clarify/smoke workflows and four original GitHub runs are retained
for comparison. No replacement workflow has been pushed or dispatched, and no
provider call was made while implementing or testing it. The user approved
configuration `3e538ec9...`, a push and one first smoke with twenty configured
proxy credits and a ten-minute timeout. No additional run or publication is authorized.

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
Copilot Chat Completions gateway with `model: auto`, `tools: []`,
`tool_choice: none`, `n: 1`, no redirect following and no retry loop. It does not launch a
Copilot CLI agent session or resolve Auto into a chosen concrete model. The
fixed local endpoint is `http://api-proxy:10002/chat/completions`; credentials
remain in AWF's proxy. This is an integration with the documented proxy, not a
claim that Copilot exposes a public direct-inference REST API.

The caller aborts after ten minutes, requests at most 2,048 output tokens, bounds
the packet to 32 KiB and provider response to 64 KiB, and accepts at most 32 KiB
of recommendation text. One fixed gateway request is enforced in caller code,
not by the previously ineffective turn setting. If the complete issue exceeds
the packet allowance, fail
preparation for human handling instead of silently truncating the report.

The new workflow has a twenty-credit proxy setting and no separate AI detector.
It has no model-selectable external action, and its trusted output is a fixed
framework no-op; the recommendation is only a raw artifact until clean Python
validation. An AI threat verdict is unnecessary for that restricted artifact
path and cannot replace structural validation. The publisher rejects this
workflow's identity. Legacy workflows retain their separate detector.

Preparation requires the new `CLARIFICATION_SINGLE_RESPONSE_ENABLED=true` switch,
main in the allowlisted repository, case 15051, run attempt one, a current signed
configuration and exactly one dispatch in this new workflow's history. Reruns and
later dispatches fail closed. The daily setting still does not constrain manual
dispatch. Reset the switch after preparation; cancel running jobs to stop them.

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

Hosted gateway compatibility, actual Auto selection, service rate limits and
account billing remain unverified for this replacement. The one-request claim is
about the caller's gateway POST; inspect proxy logs for any upstream behavior.
Local verification is recorded in `evals/evidence/single-response-verification.json`.

Verification: 67 Python tests pass, including ten Node transport/harness cases.
Python adapter line coverage is approximately 96%; the Node harness has 97.35%
line and 82.35% branch coverage. Compilation is reproducible with gh-aw v0.93.5.
The initial missing adapter and missing case-identity guard were reproduced as
failing tests before implementation/fix. These results use mocked transport only.

References: [custom harnesses](https://github.github.com/gh-aw/reference/engines/),
[AWF proxy](https://github.com/github/gh-aw-firewall/blob/v0.28.70/docs/api-proxy-sidecar.md),
[dynamic Auto accounting](https://github.com/github/gh-aw-firewall/blob/v0.28.70/docs/awf-config-spec.md).
