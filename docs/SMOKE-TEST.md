# Native automatic-selection smoke retry

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
