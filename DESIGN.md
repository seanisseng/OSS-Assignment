# Pytest bug-report clarification agent

## Purpose and measured need

The agent decides whether a maintainer can investigate a pytest report, requests
only essential gaps, stays silent on sufficient reports and defers uncertainty.
This sandbox is seanisseng/OSS-Assignment; upstream pytest is never modified.
Contextual judgement can avoid demanding OS/package lists for obvious source bugs.
A conventional field-presence checklist is retained as a reproducible baseline.

The sample is the latest 50 currently bug-labelled reports created before
1 October 2026, spanning 8 October 2024–17 September 2026. At collection,
41 had another non-bot account's response; nine remain unresolved. Median first
response among the 41 responders was 45.52 hours. Raw data and query are in
`evals/golden/audit/`; the metric does not measure effort or prove time savings.
Draft AI-assisted clarification coding finds 3/50 reports; student audit is pending.
Only matching comment excerpts were reviewed, so this is not exhaustive coding.
Label changes, edited comments/reports, imperfect bot detection, pagination and
volunteer schedules limit inference. The evidence supports an experiment, not
unattended deployment. See `audit/RUBRIC.md` for definitions and evidence IDs.

## Implementation and alternatives

Manual analysis uses Copilot via GitHub Agentic Workflows. Trusted setup exports
only approved input, instructions and skill, removing its checkout before inference.
The canonical Claude-format procedure is installed in Copilot's `.github/skills/`.
Setup hashes and explicit skill-read tool events must corroborate actual loading;
this remains remotely untested. A self-reported flag is insufficient.
The three decisions are sufficient, needs_information and human_review.
`scripts/contract.py` enforces exact fields, input hash, evidence keys, categories,
at most three questions and 1,200 comment characters. Only needs_information
can carry a comment. Missing details must matter to that particular report.

Staged safe outputs and a raw JSON artifact allow review without issue changes.
The separate publisher validates the successful same-commit analysis, trusted
pre-agent manifest, exact approved recommendation hash, maintainer role, allowlist,
sandbox label, age, duplicates, daily limit and kill switch before one bot POST.
No model-controlled repository, issue target or executable command is accepted.
Automatic failure-issue creation was found during lock-file inspection and disabled.
Analysis now has no repository write permissions or GitHub MCP read toolset.
Source: [safe outputs](https://github.github.io/gh-aw/reference/safe-outputs/).

Rejected: template completeness as the sole judge; it asks irrelevant questions
and cannot reliably recognize a clear source-level report without a reproducer.
Rejected: direct issue-triggered publication; it creates cost and spam risks.
Prevented: code execution from reporters, arbitrary browsing, upstream publication,
closing/deleting issues, merging, force-pushing and modifying pytest source.

## Evaluation and current findings

Five development and ten held-out original, unedited reports are frozen with
AI-assisted expectations revised after user-supplied AI critique and prior source. Edit history
was checked via GitHub GraphQL. This review is not independent human ground truth.
Two synthetic development diagnostics and one supplemental held-out diagnostic
add clarification coverage; the real set still has only one insufficient report.
Rule A accepts clearly specified changes and docs bugs as investigable; frozen
decision/category alternatives and primary matches are reported separately.
Later comments and expectations are not exported
to the model workspace. Student review is required before any evaluation.
Four synthetic attacks cover fake approval, impersonation, malicious tool text
and secret/foreign publication requests. Executor rejection and model resistance
are separate claims. No adversarial model transcript exists yet.

The deterministic suite tests limits, foreign targets, malformed output, stale
hashes, disabled publication, interruption, missing input and mocked publication.
A synthetic 300-request burst admits 40 attempts without any model calls.
The revised suite passes 23 tests at 96% statement coverage across the tested
safety and evaluation modules, including frozen decision/category alternatives.
These tests are mocked/local, not proof of remote execution or semantic quality.
The checklist baseline matches 5/10 drafted held-out decisions. Model accuracy,
unnecessary-comment rate, category precision/recall, abstention, relevance,
runtime and usage remain unmeasured. `dashboard.html` shows absent runs honestly.
Target: eight held-out matches, never guaranteed; preserve every failure.

## Governance and status

“Tested” below means local deterministic/mock tests unless explicitly stated.

| Control | Status and evidence |
|---|---|
| Identity | Implemented but untested remotely: Actions bot token, disclosure and run link; mock POST tested. |
| Least privilege | Implemented and tested statically: analysis lock has no write scope; publisher alone has issues:write. |
| Safe outputs | Implemented and tested locally: contract and artifact staging; remote staging untested. |
| Human approval | Implemented and tested locally: exact hash and maintainer check; protected environment proposed, not configured. |
| Budgets | Implemented and tested locally: manual dispatch, no reruns, 40 workflow attempts, five posts/day; no monetary cap proven. |
| Audit trail | Implemented but untested remotely: framework logs/artifacts, input/skill hashes, publisher output; retention 30 days. |
| Kill switch | Implemented and tested with mocks: start and final variable checks; phone rehearsal and API permission untested. |
| Drift detection | Proposed manual weekly/change-triggered reruns and semantic review within verified allowance. |
| Accountability | Implemented documentation: seanisseng owns review, configuration and emergency stop. |

Counters depend on preserved run/comment history; deleting it weakens enforcement.
Five minutes limits the agent job, not all generated support jobs. Eight model
turns and threat detection may consume additional inference. Forty analysis runs
are not forty billable calls or a $2 cap. Paid overages must stay disabled.
No inference starts while allowance is unknown; policy defaults remain disabled.

## Five required answers

1. Fake approval: report text has no authority. The executor rejects added action
   fields or foreign targets. Local rejection is tested; model behaviour is pending.
2. Model update: record actual engine/model identity and compare golden results
   weekly during active use and after changes. seanisseng reviews semantic/safety
   regressions. Requested gpt-4.1 is not a pinned model snapshot and can change.
3. 300 issues: zero automatic calls because triggers are manual. Local burst tests
   admit 40 attempts; daily publication caps at five. This is not a cost guarantee.
4. Malicious tool: it may still influence recommendation text. No tool grants
   execution, credentials or arbitrary targets. Exact human review remains needed;
   adversarial model testing and tool traces remain pending.
5. Phone stop: set enable variable false, disable both workflows, cancel active
   and queued runs, then inspect final run/comment state. Cancellation cannot undo
   posted comments. `docs/OPERATIONS.md` gives steps; rehearsal is not yet performed.

## Bill of materials

| Component | Configuration / provenance |
|---|---|
| Model/engine | Copilot; requested gpt-4.1, availability/entitlement untested, no model snapshot pin. |
| Runtime | gh-aw v0.93.5, actions pinned to full SHAs, generated CLI/container pins in lock. |
| Instructions | AGENTS.md, canonical .claude skill, analysis Markdown prompt, CONTRIBUTING.md. |
| Tools/MCP | cat, sha256sum, local file editing, framework safeoutputs MCP; no third-party MCP. |
| Permissions | Analysis read scopes; trusted publisher contents/actions read and issues write. |
| Data | Public pytest issue bodies, later comments for audit only, prior MIT source subset with LICENSE. |
| Logs/evals | Frozen hashes, 15 expectations, four synthetic cases, local tests, report/dashboard; remote logs pending. |
| Humans | seanisseng: student, reviewer, configuration owner and accountable operator. |

## Unresolved and submission gate

No push, inference, publication or same-configuration dry run has occurred.
Student expectation review, billing verification, one approved smoke test, remote
skill-loading evidence, actual evaluations and phone stop rehearsal remain required.
Live variable reads may be denied to the Actions token; fail closed and investigate.
This commit is preparation, not a completed assignment submission. The repository
submission gate must fail until actual evidence exists. No score is claimed.

AI-use statement: Codex generated the implementation, tests, draft rubric,
expectations and documentation; the assignment brief is user-provided unchanged.
Verification used local tests, coverage, compiler checks and public API provenance.
Independent student review and remote execution have not yet occurred.
