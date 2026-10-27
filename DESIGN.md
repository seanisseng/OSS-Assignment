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

The manual GitHub Agentic Workflow uses Copilot. Trusted setup exports approved
input, AGENTS.md and the canonical Claude-format skill, then removes its checkout.
The model reads untrusted issue text, historical source and simulated tool results.
Expectations and later comments are excluded. No reporter code is executed.
Network allowed is empty; GitHub tools are disabled. Hosted enforcement is untested.

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
Student status is AI-assisted pre-inference review, conditions open, not approval.
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
No inference, publication or genuine model transcript is currently recorded.
Copilot access is unverified; execution.json records pending investigation, not
an invented blocker. A dry-run submission needs a documented real execution limit.

## Governance

Tested below means local deterministic/mock tests unless stated otherwise.

| Control | Implementation and evidence status |
|---|---|
| Identity | Publisher uses Actions bot and disclosure; mock POST tested, remote identity untested. |
| Least privilege | Analysis read-only, no GitHub tool; publisher alone has issues:write; lock inspected. |
| Safe outputs | Closed contract, one staged file, size/question limits; local tests, remote MCP untested. |
| Human approval | Exact hash/maintainer check locally tested; protected environment not configured. |
| Budgets | Manual trigger, 40 workflow attempts, five posts/day, eight turns; local burst test, no cost guarantee. |
| Audit trail | Raw JSONL/output hashes, configuration/input/skill binding and assessments; real traces pending. |
| Kill switch | Disabled defaults, live variable check and cancellation runbook; mocked, not phone rehearsed. |
| Drift | Manual weekly/change-triggered golden reruns; seanisseng reviews semantics/safety; not operationally tested. |
| Accountability | seanisseng owns configuration, review, disablement and corrections; CONTRIBUTING.md. |

Deleting run/comment history weakens counters. Five minutes limits the agent job,
not all support jobs. Eight turns can entail additional provider inference.
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
| Model | Workflow requests Copilot gpt-4.1, not snapshot pinned; entitlement/reporting untested. Dry run uses actual recorded assistant identity, currently no run. |
| Runtime | gh-aw v0.93.5; action SHAs/container digests in lock; locally installed Codex CLI 0.164.0, signed in via ChatGPT. |
| Instructions | AGENTS.md, canonical .claude skill, workflow prompt, CONTRIBUTING.md; dry-run adapter in scripts/dry_run.py. |
| Tools/MCP | File write, cat/sha256sum plus compiler-added shell utilities in lock, framework safeoutputs MCP; dry-run MCP unavailable. |
| Permissions | Analysis contents/actions/issues read; publisher contents/actions read and issues write; no model-chosen target. |
| Data | Public pytest snapshots, prior MIT source; later comments are audit-only; three diagnostics and four simulated attacks. |
| Logs/evaluations | Frozen hashes, 22 inputs, deterministic tests/report/dashboard; real raw JSONL, usage and assessments pending. |
| Responsible human | seanisseng, student/reviewer/operator; partial AI-assisted review recorded without approval. |

## Unresolved and AI use

Submission remains blocked on complete review, a supported dry-run basis, fresh
execution and human assessments. Hosted identity/firewall/MCP/publication and
phone cancellation remain untested. Remote mode retains additional evidence gates.
No push or third-party resource change is authorized by local completion work.

AI-use statement: Codex wrote code, tests, draft expectations and documentation.
The user supplied the brief, partial review and revised scoring conditions.
Verification uses local tests, frozen provenance and static workflow checks;
independent human approval and real model evaluation have not yet occurred.
