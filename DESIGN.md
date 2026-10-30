# Pytest bug-report clarification study

## Purpose and evidence of need

Assess whether a pytest report permits investigation, ask only essential questions,
and defer genuine uncertainty. Contextual judgement can distinguish an investigable
source defect from a missing trigger; a template checklist cannot reliably do so.
This is a sandbox experiment in seanisseng/OSS-Assignment, not upstream deployment.

The audit sampled 50 currently bug-labelled reports created before 1 October 2026,
spanning 8 October 2024 to 17 September 2026. At collection, 41 had a detected
non-bot response and nine had none. Responders' median first response was 45.52 hours.
[Audit data](evals/golden/audit/) measures elapsed response, not effort or usefulness.
Current labels, edits, pagination, bot detection and volunteer schedules limit it.
The clarification coding is an AI-assisted draft, not an established demand estimate.

## Final architecture

Trusted Python selects a complete report, untrusted supplemental evidence and up to
four traceback-linked excerpts, within 32 KiB. Expectations, later comments and Git
history are excluded before inference. Evidence is never executed or browsed.
A custom Node harness makes one tool-free Copilot gateway request using native Auto.
No critic, repair call or agent loop runs. Output allowance is 4,096 tokens; existing
response-byte limits, five estimated proxy credits and 540-second-minus-startup
deadline remain. The outer execution step is ten minutes.

The [canonical skill](.claude/skills/bug-report-clarification/SKILL.md) and fixed prompt
request a version 2 envelope. Its unchanged eight-field recommendation is paired
with quoted supplied facts and a gap/blocker audit, one gap per question. Trusted
validation checks closed fields, source identifiers, delivered quotes and references.
It cannot judge whether a blocker is reasonable. Maintainer design choices are
separate from reporter omissions. Only needs_information has up to three questions
and a comment of at most 1,200 characters. No-action decisions have no gaps.

Exact provider responses and assistant text are preserved, including malformed
output. Derived recommendation/assessment files never repair the model response.
A fixed trusted safeoutputs CLI noop finalizes the framework; the model cannot
choose that command or publish. Analysis has read-only permissions and no tools.
The separate legacy publisher is disabled and rejects this artifact-only workflow.

The [collector](scripts/hosted_collect.py) records dispatch before sending, binds a
unique token to a run and frozen commit, and downloads independently. A lost
connection never triggers another inference. Infrastructure failures pause the
sequence; semantic mismatches and malformed outputs remain failures. One case is
archived before the next. Additional inference requires explicit authorization.

## Evaluation and findings

The frozen key has 15 real reports (five development, ten held-out), three synthetic
diagnostics and four attacks. Expectations were AI-assisted and accepted before
inference; they are not independent human ground truth. Inputs remain unedited.
The earlier configuration completed seven workflows: real decision agreement 1/5,
diagnostic agreement 2/2. Preserve [that batch](evals/evidence/development-batch-20261030/)
and [smoke failures](docs/HOSTED-ACTION-ISSUES.md) separately.

The final 22-call study awaits approval of the tested diff, configuration hash and
scope. There are no final measurements or improvement claims yet. The
[per-case review](docs/reviews/FINAL-22-CASE-REVIEW.md) records expected/actual decisions,
workflow and validation status, questions, explanations and original evidence links.
[Reproduction instructions](evals/golden/README.md) distinguish evidence completeness,
structural validity, decision agreement and observed procedural compliance.

Always-sufficient matches 13/15 real primaries and 9/10 held-out; the checklist
matches 5/10 held-out. Report development, held-out, diagnostic and attack results
separately, with reliability, unnecessary clarification, category precision/recall
and abstentions. Only one real primary requires clarification: accuracy alone can
conceal this imbalance. Frozen conditional regex scores are lexical proxies.
Small sample size, AI-assisted expectations, limited excerpts and unpinned Auto
limit generalization. A proxy estimate is not a GitHub billing deduction.

Rejected: using template completeness as the sole judge and automatic issue-triggered
publication. Prevented: model tools, closing/deleting issues, merging, force-pushing,
upstream changes, destination selection and commands chosen by model output.

## Governance status

| Control | Implementation and evidence status |
|---|---|
| Identity | Workflow/run artifacts identify the automation. No comment attribution is needed. Legacy bot disclosure has mocked tests only. |
| Least privilege | Analysis contents/actions read, tools disabled, empty network allowlist; generated lock inspected. Hosted isolation claims require evidence. |
| Safe outputs | Artifact-only envelope, bounded I/O, fixed trusted noop; exact responses retained. Structural tests do not prove semantic safety. |
| Human approval | Exact diff/hash/22-call approval precedes push and inference. Case assessments remain drafts until actual review. Publication is disabled. |
| Budgets | One request per case; 22 planned, five proxy credits each, 110 ceiling sum. Daily frontmatter is bypassed for manual runs. Paid overages stay disabled. |
| Audit trail | Native request/skill/packet/response and run/commit checks; no invented Codex events. Previous attempts preserved. Account usage recorded where available. |
| Kill switch | Launch variable checked before preparation; collector clears it in finally. Independently verify after interruption; hard kills can prevent cleanup. |
| Drift | Future use would require golden reruns weekly/after changes and semantic review by seanisseng. Final study instructions stay frozen throughout. |
| Accountability | seanisseng owns approval, settings, review and disablement; [contribution policy](CONTRIBUTING.md). |

[Artifact-only evidence mode](scripts/hosted_evidence.py) requires accurate statuses
for tested, untested, unsupported and unnecessary controls. Publication is unnecessary
here. Phone cancellation is documented but untested. Legacy evidence gates remain.
Repository was public and the launch variable false at the pre-freeze read-only check.
No ctreude invitation is needed while public. [Operations](docs/OPERATIONS.md) records
recovery and stopping procedures; no unattended deployment is claimed.

## Five required questions

1. Fake maintainer approval: the fake-approval case is among the four final attacks.
   Evidence cannot grant authority; there are no model tools. Record the actual
   decision and safety review after execution, without equating agreement to safety.
2. Provider update: Auto is unpinned. Record reported model and usage; compare golden
   tasks weekly/after changes during future use. seanisseng reviews regressions.
3. 300 issues: no automatic trigger, hence zero automatic calls. This study permits
   only the approved sequential 22. No unlimited retries or publication.
4. Malicious tool text: the malicious-tool input is simulated supplemental evidence.
   No live malicious MCP server was exercised. It can influence text, never execute
   a command; inspect output and procedural compliance before claiming resistance.
5. Phone stop: set the launch variable false, disable the workflow and cancel queued
   and running executions in GitHub Actions. Check state and recover artifacts.
   Cancellation cannot recall a sent request. No phone rehearsal is claimed.

## Agent bill of materials

| Component | Provenance |
|---|---|
| Model | Native Copilot Auto, unpinned; capture actual reported model per case. |
| Runtime | Python 3.12 standard library; Node built-ins; gh-aw v0.93.5 and SHA-pinned actions/AWF. Legacy Auto correction is hash checked. |
| Instructions | Canonical skill, fixed harness system prompt and bounded packet; AGENTS.md governs repository work. |
| Tools/MCP | No model tools. Trusted gateway POST and fixed safeoutputs noop only; simulated tool evidence is data. |
| Permissions | Artifact-only analysis read; disabled legacy publisher alone holds issues write when separately authorized. |
| Data | Public original pytest reports, pinned prior MIT source, three diagnostics, four synthetic attacks; later comments audit-only. |
| Logs/evaluations | Original bundles, native transcripts, derived outputs, frozen key, group metrics, case reviews and earlier failures. |
| Responsible human | seanisseng: student, reviewer and operator. AI assessment drafts do not substitute for student signoff. |

## Unresolved gaps and AI use

Final inference, case review, account-usage evidence and submission checks remain
pending. No final score, final commit URL or improvement is claimed prematurely.
Authenticity still depends on trusted GitHub/operator records; hashes alone cannot
authenticate fabricated logs. Model semantics, sample coverage and billing remain
limited. See the linked detailed reviews and logs rather than assuming perfection.

AI-use statement: Codex generated code, tests, documentation and draft expectations;
the user supplied the brief, critiqued and accepted the key, and set study boundaries.
Verification uses deterministic/mocked suites, pinned compilation and provenance
checks, followed by actual output review. Student understanding and final approval
remain the student's responsibility; no AI-authored review is labelled human.
