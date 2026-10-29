# Pytest bug-report clarification agent

## Purpose and evidence of need

The agent decides whether a pytest report is investigable, requests only essential
missing details, stays silent on sufficient reports and defers uncertainty.
Contextual judgement can distinguish a clear source defect from an incomplete
report; a field-presence checklist cannot reliably make that distinction.
The sandbox is seanisseng/OSS-Assignment. Upstream pytest is never modified.

The audit samples the latest 50 currently bug-labelled reports created before
1 October 2026, spanning 8 October 2024 to 17 September 2026. At collection,
41 had another detected non-bot account's response; nine had no observed response.
Median first response among responders was 45.52 hours. Raw queries and records
are in evals/golden/audit/. This measures elapsed response time, not maintainer
effort, response usefulness or demonstrated time savings. Current labels, edits,
pagination, bot detection and volunteer schedules limit interpretation.
The draft clarification count is not used as a conclusion pending a full audit.
The evidence justifies an experiment, not unattended deployment.

## Implementation and boundaries

Legacy workflows use a Copilot CLI agent. The separate single-response replacement
uses trusted preparation and a custom harness to send one bounded packet to AWF's
Copilot gateway, with the canonical skill and no model tools. Both exclude the
answer key/later comments and never execute reporter code or historical source.
Network allowed is empty; GitHub tools are disabled. Hosted enforcement is untested.

The hash-checked native-Auto launcher correction reached inference in hosted run
40827503414, but no recommendation was produced. Compile with scripts.compile_workflows;
unknown launcher bytes stop execution. Full case execution remains unverified.

The closed JSON contract permits sufficient, needs_information or human_review,
evidence keys, reasoning, approved missing-detail categories and up to three
questions. Only needs_information carries a comment, limited to 1,200 characters.
reproduction_detail names a specific missing import, fixture, layout or invocation;
a generic minimal-reproducer request does not qualify. See the canonical skill.

Analysis stages an artifact and has no repository write scope. A separate trusted
publisher checks exact approval hash, maintainer role, successful same-commit run,
trusted target mapping, allowlist, sandbox label, age, duplicates and limits.
Only that executor can POST one reviewed sandbox comment; model fields cannot
choose a destination or command. Bot attribution/disclosure is implemented locally.
The rendered comment also includes disclosure within the publisher's size limit.

Rejected: template completeness as sole judge, because it asks irrelevant questions.
Rejected: direct issue-triggered publication, because of spam and spending risks.
Prevented for the model: closing/deleting issues, merging, force-pushing, arbitrary
browsing, upstream publication and pytest changes. Publisher issues:write is broad
at the GitHub scope level, so the model is kept separate from its token and code.

## Evaluation and findings

Fifteen original unedited historical inputs retain pre-report source and license:
five development and ten held-out. Three synthetic diagnostics and four attacks
are separate, making 22 inputs. Edit provenance and expectation hashes are saved.
Student final signoff is recorded for the AI-assisted key before inference.
The nine unchanged cases and diagnostics are presented in docs/REVIEW-GUIDE.md.

Before inference, user-requested rules keep 13902 primarily sufficient and allow
human_review only when both frozen reasoning checks pass. Case 13634 has six
explicit bundles and primary {traceback, configuration}. reproduction_detail alone
is invalid. Frozen regex checks require a named detail and identify generic gaps;
they are lexical proxies and cannot replace human semantic assessment.
For 13403 only the original link/quote is saved, not the linked discussion.

Reports expose primary versus conditional decision matches, primary versus best-F1
category precision/recall and per-class results. Always sufficient matches 13/15
real primaries and 9/10 held-out; the checklist matches 5/10 held-out primaries.
Only one real case requires clarification, so recall generalization is unresolved.
An overall accuracy headline would conceal this imbalance. No model score exists.

Offline dry-run export/import and evidence checks are implemented. A fresh coding
assistant must use the same skill and prompt; its actual engine differs from Copilot.
Exports omit the answer key/history; OS-level isolation is not established by export.
Raw outputs and tool traces are archived, hash checked and reviewed; a model's claim
of loading the skill is insufficient. Invalid/interrupted attempts remain failures.
Complete explained failures can satisfy evidence completeness, not decision success.
Trace hashes detect changes but do not authenticate fabricated operator records.

Local tests cover deterministic limits, malformed output, stale hashes, isolation,
review binding, interrupted attempts and mocked publication. They do not prove
model resistance, hosted permissions or semantic quality. See evals/evidence/.
Four hosted smoke attempts failed; all remain in GitHub history. The last two
reached native Auto but ended with HTTP 429 and no recommendation. The fourth
also showed a read loop despite smaller input; see docs/HOSTED-ACTION-ISSUES.md.

## Governance

Tested below means local deterministic/mock tests unless stated otherwise.

| Control | Implementation and evidence status |
|---|---|
| Identity | Publisher uses Actions bot and disclosure; mock POST tested, remote identity untested. |
| Least privilege | Analysis read-only, no GitHub tool; publisher alone has issues:write; lock inspected. |
| Safe outputs | Replacement stages raw JSON for clean Python validation; fixed harness no-op, no AI detector; publisher rejects its workflow identity. Locally tested. |
| Human approval | Exact hash/maintainer check locally tested; protected environment not configured. |
| Budgets | Replacement: one caller gateway POST, 20 proxy credits, ten-minute abort, bounded packet/output. Fourth run's turn cap failed; manual daily check bypassed. |
| Audit trail | GitHub run traces, raw output hashes and input/skill binding; case evaluations and assessments pending. |
| Kill switch | Disabled defaults, live variable check and cancellation runbook; mocked, not phone rehearsed. |
| Drift | Manual weekly/change-triggered golden reruns; seanisseng reviews semantics/safety; not operationally tested. |
| Accountability | seanisseng owns configuration, review, disablement and corrections; CONTRIBUTING.md. |

Deleting run/comment history weakens counters. Analysis and support jobs have
separate timeouts; the fourth run did not enforce the configured turn value.
Paid overages stay disabled; do not infer a monetary cap from attempt limits.
Dry-run helpers never launch an agent or call a network; live policy stays disabled.

## Five required scenarios

1. Fake approval: issue text has no authority. Added actions/targets are rejected
   locally; model response to the saved fake-approval input remains untested.
2. Model update: record actual model/engine, rerun golden tasks weekly during use
   and after changes. seanisseng reviews regressions; aliases are not pinned snapshots.
3. 300 issues: manual triggers cause zero automatic calls. The mocked burst admits
   40 workflow attempts; five daily posts maximum. Neither is a monetary guarantee.
4. Malicious tool: untrusted text can influence a recommendation. The model has
   no publication token or destination authority. Inspect tool traces and exact
   drafts; attack decision matches alone do not establish resistance.
5. Phone stop: set CLARIFICATION_ENABLED false, disable both workflows, cancel
   queued/running executions and inspect comments/run state. Already posted comments
   cannot be recalled by cancellation. docs/OPERATIONS.md is an untested rehearsal.

## Agent bill of materials

| Component | Provenance and status |
|---|---|
| Model | Native Auto, unpinned; third smoke response usage identifies gpt-4o-mini-2024-07-18. See docs/HOSTED-ACTION-ISSUES.md. |
| Runtime | gh-aw v0.93.5 and pinned actions/AWF; replacement Node 24 harness uses built-ins, not a CLI agent session. Legacy dry-run uses Codex CLI. |
| Instructions | AGENTS.md, canonical .claude skill, workflow prompt, CONTRIBUTING.md; dry-run adapter in scripts/dry_run.py. |
| Tools/MCP | Replacement model has no tools; trusted harness uses the fixed AWF Copilot gateway. Legacy file/shell/MCP configuration remains for comparison. |
| Permissions | Analysis contents/actions/issues read; publisher contents/actions read and issues write; no model-chosen target. |
| Data | Public pytest snapshots, prior MIT source; later comments are audit-only; three diagnostics and four simulated attacks. |
| Logs/evaluations | Frozen hashes, 22 inputs, tests/dashboard; four hosted failures, latest proxy usage 17.19639 credits; assessments pending. |
| Responsible human | seanisseng, student/reviewer/operator; AI-assisted key approved before inference. |

## Unresolved and AI use

The [hosted failure record](docs/HOSTED-ACTION-ISSUES.md) documents four failures.
The [replacement](docs/SINGLE-RESPONSE-REVISION.md) is implemented and mocked:
one bounded issue/skill/excerpt packet, no model tools and one caller request.
Clean Python validation remains separate; actual gateway/Auto compatibility and
semantic skill compliance remain unverified. Excerpt omissions risk abstention.
Submission remains blocked on fresh execution and human assessments.
Hosted identity, firewall, MCP, publication and phone cancellation remain untested.

AI-use statement: Codex wrote code, tests, draft expectations and documentation.
The user supplied the brief, reviewed the key and gave final signoff.
Verification uses local tests, frozen provenance and static workflow checks;
the user approved one replacement smoke; completed case evaluation remains pending.
