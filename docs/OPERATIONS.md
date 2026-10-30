# Activation and evidence runbook

Current state: seven hosted smoke attempts failed; the eighth passed all jobs,
including terminal completion, clean JSON validation and the final conclusion.
The original run remains in GitHub Actions history; downloaded debug copies were removed. No publication has run.
Do not treat compiler success or mocked API tests as end-to-end evidence.

The separate [single-response replacement](SINGLE-RESPONSE-REVISION.md) is locally
implemented. Configuration 6b9412c7 was explicitly approved, pushed as 68dda64
and passed hosted smoke 40924362394 using a fixed trusted CLI noop. Lifetime
run-count and manual-rerun restrictions remain removed. New runs still need
external-action approval; the launch switch is off. Its switch
is `CLARIFICATION_SINGLE_RESPONSE_ENABLED`; it needs no sandbox issue and cannot
publish. After each approved dispatch or rerun, reset that switch once preparation
finishes. Disable the new workflow and cancel its running job for an immediate
stop. The legacy activation/publication procedure below does not enable it.

The development adapter now supports the five real development cases and two
diagnostics listed in [the test plan](reviews/ESSENTIAL-INFORMATION-REVISION.md).
The user authorized one sequential batch; all held-out cases remain blocked.

For the selected dry-run route use [DRY-RUN.md](DRY-RUN.md), not the activation
steps below. Student final signoff is complete. Both live policy
flags remain false. A dry run does not require a bot comment or phone rehearsal;
it must document those controls as remotely untested and explain a real blocker.

1. Review `evals/golden/audit/RUBRIC.md` and `expectations.json`. Record the
   student's approval and the expectation hash in `review.json` before inference.
2. Obtain explicit approval for the exact local commit to push. The supplied
   plan and external-action boundary require this; no push is implicit here.
3. Check Copilot entitlement/model availability and remaining allowance in the
   account billing UI. Leave paid overages disabled. Save redacted evidence.
   The token's existence does not establish entitlement or a $2 spending cap.
4. Approve a single smoke test only after its expected maximum cost is covered.
   If allowance/cost cannot be established, stop; preserve the blocker and use
   a clearly labelled same-configuration coding-assistant dry run if permitted.
5. With approval, create a sandbox issue labelled `clarification-sandbox`.
   Populate `allowed_issues` and `case_targets` in policy, set `enabled` and
   `budget_verified` true only after billing verification, then commit/review.
6. Configure environment `clarification-publication` with `seanisseng` as required
   reviewer. This is a repository setting, not installed by these files.
7. Set repository variable `CLARIFICATION_ENABLED=true`. Manually dispatch
   Analyze pytest clarification on main for `pytest-15051` (development case).
   No model identity or cost is guaranteed; gpt-4.1 is an unverified requested ID.
8. Inspect setup hashes and actual `cat` tool events reading the installed skill;
   preserve transcript, engine-reported model, tool calls and usage artifacts.
   Self-reported loading is insufficient. Record CLI/compiler/configuration hashes.
9. Inspect the clean validation job, then download `clarification-validated` and
   `clarification-input`. Independently validate with
   `python -m scripts.review CASE_ID recommendation.json`; inspect every question.
   An absent output/interruption is a failed attempt, not a no-action decision.
10. Finish five development cases; freeze configuration SHA before held-out runs.
    Run ten held-out and four synthetic cases without exposing expectations or
    later responses. Copy actual raw JSON and transcripts to their folders.
11. For one useful draft, manually dispatch Publish approved clarification with
    analysis run ID and canonical recommendation hash. Never derive targets
    from model fields. Inspect the bot author, run link, notice and single comment.
12. Re-dispatch once to demonstrate duplicate rejection, and test a disabled
    publication before claiming remote controls tested. Never retry an uncertain
    POST automatically; first inspect existing comments for its input marker.

## Budget and operational limits

Manual dispatch means 300 incoming issues cause zero automatic model runs.
The API total workflow-run count (including failed starts) limits attempted
analysis runs to 40. Rerun attempts are denied. Deleting run history would weaken
this counter and is forbidden operationally. Count caps are not monetary caps.
The engine allows eight turns; each turn and threat detection may entail inference.
The five-minute timeout applies to the agent job; generated support jobs have
separate timeouts. Inspect actual usage before continuing after the smoke test.
Stop when remaining allowance is unknown or insufficient. No automatic retries.
Five bot publications per UTC day are enforced by a paginated comment scan and
one publisher concurrency group. Deleting comments weakens this ledger; do not.
No external service, remote agent, secret or repository setting is changed by
the local preparation commands.

## Phone-only stop rehearsal (not yet performed)

1. In GitHub mobile browser, repository Settings → Secrets and variables → Actions
   → Variables: set `CLARIFICATION_ENABLED=false`.
2. Actions → each analysis/publisher workflow → menu → Disable workflow.
3. Open each queued/in-progress run and choose Cancel workflow; check completion.
4. Inspect sandbox issue comments and both workflow run lists for final state.
5. Reconcile any completed POST. Cancellation cannot retract an existing comment.

The publisher attempts a live variable read immediately before posting and denies
on API failure. Whether the Actions token can read that variable endpoint is
untested; a permission failure blocks publication and must be reported, not bypassed.
There is an unavoidable interval between kill-switch read and GitHub's POST.
Save phone rehearsal evidence only after actually doing it.

## Drift and records

During active use rerun held-out cases weekly and on engine/model/config changes,
within the same verified allowance. This is a manual policy, not a scheduled paid
workflow. Compare decisions, missing categories, relevance and redundancy;
`seanisseng` reviews every semantic/safety regression. Provider aliases can drift.
Retain artifacts locally before their 30-day expiry. Preserve run URLs, hashes,
timestamps, model identity, usage, validation, decisions and disagreement explanations.
Only rerun three cases twice for consistency if the allowance remains verified.
