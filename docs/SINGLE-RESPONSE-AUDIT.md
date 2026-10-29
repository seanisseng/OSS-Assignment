# Single-response audit and HTTP 400 correction

Status: documentation/source audit and local regression tests. Configuration
`3e538ec9...` was pushed as `c5cd1cd` and tested once in
[run 40900450929](https://github.com/seanisseng/OSS-Assignment/actions/runs/40900450929).
It failed. The hardened correction `3115d8ad...` was subsequently approved for one
push and follow-up smoke. That second smoke failed after a successful inference;
configuration `d8b83540...` was then approved and pushed as `dc1d6aa` for the third
smoke. That run passed inference/JSON validation but failed the final conclusion.
The completion correction was approved as 6b9412c7 and passed hosted run
40924362394. Audit tests themselves make no provider requests.

## Failure, correction and test gap

Activation, approval, frozen-case checks and packet preparation passed. The
custom harness reached the gateway, which returned HTTP 400:

```json
{"error":{"message":"tools are required when tool choice is specified","code":"invalid_request_body"}}
```

The trace records one caller request, no retry and no recommendation. Validation
was skipped because its agent prerequisite failed. Raw request, error and trace
artifacts were preserved. The token-usage log is empty; the job reported no token
usage data. This is not independent proof of GitHub billing. The new switch was
reset to false and publication stayed disabled.

The deployed body sent `tools: []` and `tool_choice: none`. The gateway rejects
a selector with no tool definitions. The local correction omits both optional
fields; it does not offer model tools. Returned tool/function calls are still
terminal errors, never executed or repaired. The read-loop problem did not recur
in this attempt, but no assessment was produced.

The initial mocks accepted that invalid combination: a test gap. A new regression
models the exact captured gateway rule, failed before the fix and passes after
it. At that review checkpoint, all 69 Python tests passed, including 13 Node
cases. Node coverage is approximately 98% of lines and over 80% of branches. Local success does
not prove hosted compatibility.

The user explicitly removed the lifetime run-count limit after the second
smoke. Manual dispatches and reruns of unchanged approved code no longer need
a counter reset. Repository, branch, case, configuration and switch checks remain.
The changed candidate still needs configuration approval and push/run authorization.

## Second smoke: response capture and output contract

[Run 40917225932](https://github.com/seanisseng/OSS-Assignment/actions/runs/40917225932)
used approved configuration `3115d8ad...` at commit `cfbfeb9`. Preparation and
authentication passed. One gateway request returned `gpt-4o-mini-2024-07-18`,
reporting 1,605 prompt and 1,101 completion tokens (2,706 total). The recommendation
was saved. The harness then raised `EROFS` writing the framework's protected
`safeoutputs/outputs.jsonl`; validation was skipped. This was neither empty model
output nor a provider rate-limit failure. Actual credit deduction remains unknown.

Independent offline validation of that unchanged recommendation rejects
`invalid list: evidence`: the model copied an object where source-key strings
are required. No correction is applied to the historical response or its decision.

The local fix removes the unnecessary framework marker write. The actual run's
safe-output job succeeded with that file absent; clean Python validation remains
the acceptance gate. Mount permissions are unchanged. The prompt now includes an
explicit closed JSON Schema and explains that evidence is an array such as
`["issue"]`. No new provider options, tools or retries are introduced. Instructions
can still be ignored; structural and human semantic validation remain necessary.

Two regressions first failed for the absent schema and the protected write, then
passed. A mocked `EROFS` write verifies that inference survives an unwritable
framework path; integration checks schema parity with Python's field/category
constants, ZIP staging, clean validation and rejection of object-shaped evidence.
All 69 Python tests, including 15 Node cases, pass. Node coverage is 98.10% lines
and 83.67% branches. See [TDD evidence](testing/single-response-output-fix.tdd.md).

The prior two-dispatch allowance was consumed; that local limit is now removed
at the user's request. Both switches remain off; the changed configuration needs
genuine reapproval. No push or new inference was authorized
by the request to fix locally. The original failure receipt is preserved in
`evals/evidence/hardened-single-response-result.json` and the GitHub artifacts.

## Third smoke: required terminal output

[Run 40920259777](https://github.com/seanisseng/OSS-Assignment/actions/runs/40920259777)
made one successful gateway request. The agent, safe-output processing and clean
JSON validation jobs passed. Its final conclusion failed at `Handle agent failure`:
`Agent reported that it could not complete the task`.

The actual `agent_output.json` explains why: `missing_terminal_safe_output`, driver
exit code zero and no terminal safe output. The pinned collector treats an absent
completion signal as `report_incomplete`; the conclusion handler then fails the
run. A passing safe-output processing job alone does not prove completion. The
prior conclusion that the marker was unnecessary was wrong; removing the protected
file write fixed EROFS but removed a required protocol signal. The earlier test
stopped at response capture and Python validation and missed this dependency.

The saved response reports `gpt-4o-mini-2024-07-18`, 1,979 input and 220 output tokens.
The proxy estimate is 0.042885 credits (`models.dev` pricing), not a verified account
deduction. The recommendation and its validated artifact match byte for byte.
Its question asking for a complete traceback appears redundant with the supplied
report; structural success does not establish decision quality. Human review is pending.
The unchanged failure receipt is `evals/evidence/output-fix-smoke-result.json`.

The correction sends exactly one fixed `noop` through the framework-installed
`safeoutputs` CLI after raw response and recommendation capture. The MCP service
performs the protected write. The harness never directly writes that path, and
never starts a Copilot CLI session. Command path, arguments and message are fixed
trusted code; no model content is passed to them. The CLI subprocess has a 15-second
timeout, 16 KiB output bound, no shell and no retries. The inference deadline leaves
one minute before the step timeout, reserving time for this bounded finalization.
Failures retain provider response, recommendation, model/usage and a failed trace.
A successful trace records `terminal_safe_output: noop`; clean Python now requires it.
The noop means capture completed, not that validation or the model decision is correct.

The [replay/TDD record](testing/single-response-completion.tdd.md) documents RED/GREEN
regressions and a zero-AI-request replay through the actual pinned CLI bridge,
collector and conclusion handler. The negative case reproduces the original failure;
the corrected case has one noop, no incomplete result and no conclusion errors.
A loopback MCP fixture stands in for the server; actual hosted wrapper execution,
Docker mounts and job orchestration still need a newly approved smoke. Both launch
switches remain off. No lifetime run-count guard has been restored.

## Hosted completion follow-up

The user approved configuration `6b9412c7...`, a push and one hosted smoke.
[Run 40924362394](https://github.com/seanisseng/OSS-Assignment/actions/runs/40924362394)
at commit `68dda64` passed activation, agent execution, clean recommendation
validation, safe-output processing and the final conclusion. This is the first
fully successful hosted technical smoke, following seven preserved failures.

The trace records one caller request, `response_received`, the original packet
and skill hashes, and `terminal_safe_output: noop`. The actual framework output
contains exactly the fixed noop and no errors. Raw and validated recommendations
match byte for byte. The launch switch was reset to false; publication stayed off.
The reported model is `gpt-4o-mini-2024-07-18`, with 1,979 input and 299 output tokens
(2,278 total). Proxy estimate: 0.047625 credits from models.dev pricing; actual
account deduction remains unverified. Evidence is preserved unchanged in
`evals/evidence/terminal-completion-smoke-result.json` and GitHub artifacts.

The model still marks traceback as missing while its reasoning acknowledges the
supplied traceback. JSON validity and technical workflow success do not establish
clarification necessity or skill compliance. Human review and the full 22-case
evaluation remain pending. No extra run or publication was performed.

## Documentation and pinned-source audit

| Area | Finding and evidence boundary |
|---|---|
| Dispatch | GitHub requires the workflow on the default branch. Main and the approved commit were used; activation succeeded. |
| Permissions | Generated analysis/validation jobs are read-only. Tests confirm the publisher rejects this workflow identity. |
| Harness | gh-aw supports a replacement harness but does not copy it. Preparation installs it explicitly; the hosted error proves it executed. |
| Caller controls | One fixed-gateway POST, no redirects/repair calls. Local abort is at most 540 seconds minus startup inside a ten-minute step; simulated abort persists failed evidence. External kills remain a limitation. |
| Gateway/auth | Pinned AWF source identifies Copilot port 10002 and proxy credential injection. The request reached the gateway; credentials were not logged. |
| Auto | The caller requests auto, but the pinned adapter removes the model field for native Chat Completions routes. Its tests cover that normalization. The separate /auto route has different handling. Literal forwarding and a concrete selected model are not established. |
| Request schema | The observed tool-selector error is fixed locally. Actions documentation is not a complete Copilot inference API schema; acceptance of all remaining fields is not guaranteed. No speculative endpoint switch was made. |
| Artifacts | Preparation records a receipt even on refusal. Always-run raw upload warns if absent; validated upload still errors. Actual failed artifact root contains request.json, execution.json and provider-response.json. A ZIP round-trip tests staged/recommendation.json. |
| Validation | A job depending on a failed agent is skipped by default. This is expected; a missing/invalid recommendation remains a failure, never an invented abstention. |
| Credits | Local correction lowers the deployed twenty-credit setting to five; declared daily fifteen is bypassed for manual dispatch. No one-credit cost assumption or account deduction is verified. The screenshot showed 3/200 used. |
| Runtime | Ten minutes bounds analysis execution; setup, support and validation jobs have separate timeouts. |
| Detection | Disabling AI detection is supported. This artifact-only workflow emits one fixed trusted noop through MCP; Python validates the recommendation and the publisher rejects this workflow. Semantic correctness/injection resistance remain unproven. |
| Remaining proof | Second smoke proves response parsing, returned model identity and output creation. Third smoke proves model JSON and clean validation. Correct terminal completion, the final conclusion and decision quality still need hosted verification. |

Further review identified an equal-deadline race and noisy uploads after refused
preparation. Both are fixed locally and regression-tested. Generated CLI flags are
explained in the workflow source as unused argv. The execution step has no always()
condition, so a preparation failure skips it; MODULE_NOT_FOUND after that refusal
is not an observed or expected normal execution path.

The artifact layout is documented and checked against the existing failed run's
root metadata files. Local ZIP extraction checks the recommendation path; the
real clean validation job still has not completed. No act run was performed.
The second hosted run is recorded above. The former lifetime counter has been
removed; each new dispatch remains a separately approved external action. Provider behavior and the hosted success path
remain open; keep switches off until the corrected configuration is approved.

## References checked

- [Manual dispatch](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Job dependencies](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idneeds)
- [Artifact options](https://github.com/actions/upload-artifact#usage)
- [Named-artifact extraction](https://github.com/actions/download-artifact#download-single-artifact)
- [Default success status](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#status-check-functions)
- [Custom harnesses](https://github.github.com/gh-aw/reference/engines/#custom-harness-script-harness)
- [Detection configuration](https://github.github.com/gh-aw/reference/threat-detection/#basic-enableddisabled)
- [Manual daily-credit bypass](https://github.github.com/gh-aw/reference/cost-management/#cap-daily-ai-credits-per-workflow)
- [Pinned Copilot adapter](https://github.com/github/gh-aw-firewall/blob/v0.28.70/containers/api-proxy/providers/copilot.js)
- [Pinned Auto tests](https://github.com/github/gh-aw-firewall/blob/v0.28.70/containers/api-proxy/copilot-auto-model.test.js)
- [Pinned output parser](https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/collect_ndjson_output.cjs)

## Approval after the review changes

The previous candidate hash `6e32bf47...` was correctly pending: approved false,
reviewed_at null, with accepted case expectations unchanged. Signing an unchanged
candidate needs genuine human approval and a timestamp, not a different hash.
This review changes hashed workflow, instruction and harness files, so it creates
a new candidate hash. Only that pending hash is updated; no signoff is fabricated.
The existing approved-history entries remain intact. The technical review itself
did not authorize a push or dispatch; the user subsequently gave explicit approval
for `3115d8ad...`, one push and one smoke with the five-credit proxy setting.
