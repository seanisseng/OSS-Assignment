# Activation and evidence runbook

The version 3 capture is finished: 19 hosted attempts, three hosted cases unrun,
and six separately authorised dry-run assessments. All 22 assessments are signed,
including a corrected second revision for pytest-13403. Publication remains disabled.
Start with [the experiment review](EXPERIMENT-REVIEW.md) and run
`python -m review_tools verify` then `python -m review_tools report`.
These commands make no network or model calls. [Prepare-only reproduction](DRY-RUN.md)
does not authorise new execution. The procedures below are retained as history.

The previous seven-case development batch completed all seven workflows, with
1/5 real decision matches and 2/2 diagnostic matches. Preserve it under
`evals/evidence/development-batch-20261030/`; it is a different configuration.
Earlier smoke failures remain in [the hosted history](HOSTED-ACTION-ISSUES.md).

## Historical study capture procedure

The [freeze packet](FINAL-STUDY.md) describes version 2; version 3 has its own
[pre-registration](V3-PRE-REGISTRATION.md). The commands below describe the old
final-ledger capture, not instructions to redispatch the completed study.
Complete runtime, collector and evidence changes and run all pre-freeze checks.
Present the tested diff, hash and 22-call scope for explicit approval. Do not push,
enable the switch or dispatch before that approval. Record the actual approval;
do not invent a student review. Leave paid overages disabled and record available
account usage before and after, including unavailable fields and their reason.

After approval, create the inference commit, push it and initialize the ledger:

```text
python -m scripts.hosted_collect init --study evals/golden/hosted/final --commit FULL_SHA
```

Bind the plan's approval to the user's actual approval record. `run` handles one
case, enables the switch, records its dispatch first, binds the unique token to a
run, waits, downloads and imports evidence, then clears the switch in `finally`.
Use the order in `scripts.single_response.CASE_ORDER`: five real development,
two development diagnostics, ten held-out real, the remaining diagnostic, four
adversarial. Archive a case before beginning the next. Never change instructions
once final inference starts. Do not use workflow reruns.

```text
python -m scripts.hosted_collect run --study evals/golden/hosted/final --case CASE_ID
```

A connection failure never authorizes another inference. Find the existing run by
its ledger token, then recover with `bind`, `download` and `import`; these commands
do not dispatch. Refusals, cancellations and failed outputs stay in the archive.
Infrastructure/authentication/throttling failures pause the sequence. An additional
inference requires explicit authorization and disclosure; it is not part of an
identical 22-call study. Invalid model output and semantic mismatches remain failures
and do not themselves justify a retry. A hard process kill may interrupt switch
cleanup: independently confirm the variable is false after interruption/completion.

For an immediate stop on a phone: open repository Settings / Actions / Variables,
set the launch variable false; open Actions, disable this workflow and cancel every
queued/running execution. Confirm state after cancellation and recover artifacts.
This procedure is documented, not a tested phone rehearsal. It cannot revoke a
request already sent or recover evidence lost to abrupt cancellation.

Original bundles live under `evals/golden/hosted/`; canonical recommendations,
transcripts and draft assessments are populated by import. Review every actual
question against delivered facts, implied facts, expected decisions and blockers.
Record only actual review identities/times. Model audit text is not human approval.

```text
python -m scripts.evaluate --mode single-response
python -m scripts.final_report
python -m scripts.verify --submission --mode single-response
```

Complete `evals/evidence/single-response-controls.json` with accurate statuses and
hashed evidence. Publication is unnecessary for artifact-only submission. Do not
require a publication or phone-cancellation test to pass this mode. Legacy dry-run
and remote modes retain their earlier evidence requirements. Scan tracked files
for credentials/caches, review the final diff and request approval of the exact
submission commit before pushing. Verify that commit's required files and links.

## Historical legacy activation procedure (not the final study)

The following applies only to the older multi-turn/publishing workflows. Its
publication and phone rehearsal steps are not final artifact-only submission gates.

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
