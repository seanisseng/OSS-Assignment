# One-case hosted smoke test

Status: prepared and locally tested; not dispatched. On 29 October 2026 the user
approved this smoke configuration, push to main and one dispatch. review.json binds
the new configuration and retains the earlier approval; the answer key is unchanged.

## Exact proposed execution

- Repository and branch: seanisseng/OSS-Assignment, main.
- Workflow: .github/workflows/smoke.lock.yml; input case_id=pytest-15051 only.
- Engine: existing Copilot credential, model selector auto, eight turns maximum.
- Agent timeout: five minutes, with separate support-job timeouts.
- Proxy credit limits: ten for analysis, five for output threat detection;
  fifteen for the workflow's rolling daily guardrail. Hosted enforcement is untested.
- Dedicated variable: CLARIFICATION_SMOKE_ENABLED=true for the single attempt.
- The preparation rejects reruns and any second dispatch, including after failure.
- Outputs: input manifest, raw recommendation, validated recommendation and logs.
- Publication: no sandbox issue is created or targeted. Existing policy stays disabled;
  the publisher rejects analysis runs whose source is smoke.lock.yml.
- No paid overages, new credentials, upstream changes or additional model runs.

The procedure uses the same canonical skill, AGENTS.md and agent prompt as clarify.
Only trusted setup, the Auto selector, spend guardrails and workflow identity differ.
Record the actual routed model if provided; Auto is not a pinned model snapshot.

## Before dispatch

1. Approve this exact change and upload/push the signed-off files and smoke files
   to main. Do not include unrelated edits to the assignment brief.
2. Bind review.json to the new configuration hash, retaining prior approval history.
   Keep the original expectation hash; no expected decision has changed.
3. Use the owner's authenticated GitHub session. The connected GitHub app currently
   identifies another account with read-only access; existing Git credentials are
   unavailable noninteractively. Do not extract tokens from the browser or Desktop.
4. Verify current allowance in the browser and keep additional paid usage disabled.
   A 15-credit configured guardrail is not remote evidence of a precise spending cap.
5. Enable only the smoke variable, dispatch once, and preserve the run URL.

## After the attempt

Disable the smoke variable and preserve all logs/artifacts, including failures.
Check actual skill-read events, input/skill/config hashes, raw JSON and validation.
Compare the result against the frozen expectation only after inference. Ask the
student to assess reasoning, essentiality, redundancy and safety; do not invent
their assessment. Record credits before/after and provider usage where available;
billing display latency or other account activity can limit attribution.

Stop after this attempt. Do not start the remaining evaluation without reviewing
the result and remaining allowance. The remote transcript importer still needs
verification against a genuine Copilot trace; preserve raw artifacts independently.

## Local verification

The new smoke tests first failed because scripts.smoke did not exist. After
implementation, Windows temporary-directory ACLs prevented sandboxed execution;
the same tests were run outside the sandbox with mocked GitHub calls.
All 49 deterministic tests passed, including stale-review/input rejection,
wrong-repository/branch/case checks, retry/second-dispatch rejection and publisher
rejection of the smoke workflow. No inference ran in those tests.

Compiled using gh-aw v0.93.5 and the existing pinned release action SHA.
python -m scripts.verify and git diff --check passed. No historical input,
source context or audit record was changed.
