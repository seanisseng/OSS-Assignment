# Native automatic-selection smoke retry

Historical retry notes; the hosted result below supersedes earlier pending claims.
See [the complete failure record](HOSTED-ACTION-ISSUES.md) and
[the current pending configuration](SIMPLIFIED-WORKFLOW.md) for current status.

The user authorized one replacement attempt on 29 October 2026. Case: pytest-15051.
The first run remains in GitHub Actions history; local debug downloads were removed
at the user's request. It failed before a model response and reported zero usage.

## Configuration

The existing Copilot credential is used. COPILOT_MODEL is explicitly empty in the
analysis and detection environments, allowing native Copilot automatic selection.
No --model argument is emitted. The skill, prompt and answer key are unchanged.

Analysis has a ten-credit configured proxy limit, detection five, and the rolling
daily guardrail fifteen. Paid overages remain disabled. Hosted enforcement and
successful native Auto are not yet claimed tested by this configuration.

Preparation accepts only case 15051, main in seanisseng/OSS-Assignment, workflow
attempt one and total dispatch count exactly two. A third dispatch and GitHub
reruns fail closed. The original failed run must not be deleted to reset counters.

Publication remains disabled. No sandbox issue is targeted. The publisher rejects
this workflow's artifacts. CLARIFICATION_SMOKE_ENABLED is enabled only for setup
of this attempt and reset to false after preparation or failure.

## Validation and next step

All 50 deterministic unit/mocked integration tests passed; the workflow compiled
with the existing gh-aw v0.93.5 and pinned action SHA. The review binds the corrected
configuration hash. No historical report or expected outcome was changed.

Inspect the actual outcome, skill-read events and usage after this single attempt.
Do not launch the remaining evaluation or automatically retry. A correct decision
still needs the student's semantic assessment. GitHub's original logs remain the
source for each run; no failed output is repaired or reported as a no-action result.

## Outcome

The replacement run failed before a model response because the hosted BYOK-style
provider requires an explicit model. Native automatic selection remains unresolved.
The smoke switch is off and publication remains disabled. Both original runs
remain in GitHub Actions history; downloaded first-run debug copies were removed.

## Prepared compatibility correction

See STUDENT-AUTO.md for the new hash-checked native-Auto correction. It keeps an
explicit auto selector, the proxy and credit limits. One prospective verification
attempt is restricted to dispatch count three; configuration approval and the
smoke switch are both required before it can run. No third attempt has launched.

## Hosted verification result

Run 40827503414 completed with failure. Native Auto reached the provider and the
canonical skill was actually read. The model delegated and repeatedly tried to
read/search the large compact case JSON, then hit GitHub rate limiting. No
recommendation file exists, so this is not a successful end-to-end evaluation.
Proxy-reported usage was 10.08027 analysis credits and 0.28257 detection credits;
final account billing is unconfirmed. The detector also hit rate limiting.
The smoke switch is off, publication stayed disabled and no further run started.
Temporary debug downloads were removed after inspection; GitHub retains the logs.
