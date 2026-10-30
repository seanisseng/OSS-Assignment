# Essential-information procedure revision

Status: local instruction candidate; behavioural improvement has not been measured.
AI-assisted revision requested by the user after reviewing run 8. It changes the
canonical skill only, with no case-specific expected answers in the instructions.

## Problem and unchanged baseline

[Run 8](https://github.com/seanisseng/OSS-Assignment/actions/runs/40924362394) passed
the technical workflow but returned needs_information for development case 15051,
whose accepted pre-inference decision is sufficient. It marked traceback missing
while acknowledging one, asked a generic configuration question, and asked a version
question without listing versions as a missing category. See the
[review document](RUN-8-PYTEST-15051.md).

The original recommendation remains unchanged in
`evals/evidence/terminal-completion-smoke-result.json`. All seven failed execution
attempts remain preserved too. The frozen inputs, expectations, scoring functions,
held-out split and human-assessment records are unchanged. This proposal does not
retroactively turn run 8 into a successful decision or a test of the new skill.

## Before and after

| Area | Previous procedure | Revised procedure |
| --- | --- | --- |
| Supplied information | Said to identify the concrete failure and use a traceback or relevant code when sufficient | Explicit inventory separates supplied facts, unambiguous implications and unknowns before choosing gaps |
| Essential gap | Said information must block investigation | Requires a named absent detail and the specific investigation step that cannot begin without it |
| Generic questions | Limited redundancy and relevance | Explicitly rejects template-completion questions and asks what ambiguity a version, configuration, OS or command answer would resolve |
| Expected behavior | Rule A distinguished maintainer acceptance from missing information | Also says not to make the reporter design a fix or restate an unambiguous contrast before investigation |
| Internal consistency | No explicit category/question self-check | Each category must map to a question; each question to a category; reasoning must not declare acknowledged evidence missing |
| Justification | Explain each essential gap | Concise evidence and blocker justification inside the existing reasoning field; no additional fields or hidden transcript |

The revised procedure still permits needs_information for a genuine missing
blocker and human_review for genuine uncertainty, conflicting evidence or scope.
It does not force every traceback-containing report to sufficient. It does not
invent an answer from omitted files or require all metadata to be present.

The fixed JSON contract, Auto model selection, tool-free model request, completion
CLI, one-request limit, budget, timeout and manual launch switch are unchanged.
The case adapter now permits exactly the seven development inputs listed below;
clean validation binds the manifest to the case selected in that dispatch.
No regex or heuristic silently rewrites a model decision. Category/question
consistency remains an instruction and a review criterion, not a new semantic
claim made by the deterministic validator.

## Local verification and its limits

Executed: `python -m unittest discover -s tests -v` and `python -m scripts.verify`.
All 70 Python tests pass, including the 18 Node transport/harness cases.
Mocked integration covers all seven cases; held-out IDs, path traversal and
cross-case artifacts are rejected. Python adapter line coverage is 95.14%. Existing
integration checks cover delivery of actual skill content, hash binding, response
capture, completion acknowledgement and the closed output contract.

All 22 original input packets still fit within 32 KiB without truncating their
reports. The revised 15051 packet is 8761 bytes; the largest is
22097 bytes. These are packet checks, not new model assessments.
No hosted request or additional inference was performed for this revision.
Static checks or a mocked model response cannot prove semantic improvement.
The baseline decision failure is real; a behavioural GREEN result remains pending.

## Development check before held-out evaluation

Use the established development split and two existing diagnostics first. The
expectations below are copied from the frozen key for reviewer planning only;
they must not be supplied in inference packets. Synthetic diagnostics do not
count as real historical examples in assignment metrics.

| Case | Type | Frozen expected decision | Revised-skill result |
| --- | --- | --- | --- |
| pytest-15052 | Real development | sufficient | Not run |
| pytest-15051 | Real development | sufficient | Not run |
| pytest-13403 | Real development | human_review | Not run |
| pytest-13986 | Real development | sufficient | Not run |
| pytest-13716 | Real development | sufficient | Not run |
| diagnostic-crash | Synthetic diagnostic | needs_information | Not run |
| diagnostic-trigger | Synthetic diagnostic | needs_information | Not run |

For every attempt, preserve the exact configuration and input/skill hashes,
request/response, returned model identity, usage and failures. Use fresh sessions
with no answer-key or review-document access. Review these questions:

1. Does the recommendation accurately name the evidence already supplied?
2. For each question, is the missing detail actually absent, and what named
   investigation is blocked without it? Merely helpful information is insufficient.
3. Do missing categories, questions and the explanation agree? Does the reasoning
   acknowledge information that missing simultaneously declares absent?
4. Does the decision match the frozen key? If not, record the disagreement and
   human assessment rather than changing the key to fit the response.
5. Do both genuine-clarification diagnostics and the human_review case still
   receive appropriate decisions, avoiding an overcorrection toward sufficient?

Predeclare one attempt per selected case for the initial comparison, report every
outcome, and do not rerun until a favourable answer appears. This is an evaluation
plan, not a reinstated runtime limit or authorization to dispatch paid runs.
If development findings warrant another revision, preserve each version and its
failures. Freeze the chosen configuration before inspecting held-out outcomes.
The full evaluation must still compare actual output with prior expectations for
every case and report failures; the assignment does not require perfect accuracy.

## Execution readiness and approval

The adapter now offers the exact seven-case menu and independently enforces it
in trusted preparation and clean validation. The ten held-out cases remain
blocked. No critic agent or extra model call is added.

The user explicitly requested running the development workflow after the local
implementation. The operator will launch one run per selected case, sequentially,
and preserve successes, semantic mismatches and invalid outputs. Infrastructure
failures stop the remaining batch rather than repeatedly consuming requests.
There is no automatic retry and no reinstated lifetime testing counter.

Existing per-run proxy setting: five credits. Seven runs therefore have a sum of
per-run ceilings of 35 proxy credits; this is not a verified account charge or a
new enforced daily cap. Manual dispatch bypasses the declared daily guard. No
publication is enabled. Local operation requires this computer to stay awake.
The exact approved configuration and results are recorded separately. No completed
human assessment is created from this AI-authored plan.

## Assignment and review references

- [Operative assignment brief](../../assignment_instructions_updated.md), testing and design requirements.
- [Canonical revised procedure](../../.claude/skills/bug-report-clarification/SKILL.md).
- [Frozen development split and expectations](../../evals/golden/expectations.json).
- [Dry-run protocol](../DRY-RUN.md), development-before-held-out order and human assessments.
- [Run 8 review](RUN-8-PYTEST-15051.md), exact original output and pending student questions.

AI-use statement: Codex drafted this revision and plan. Local tests verify delivery
and mechanics; no claim of improved model decisions is made before fresh testing.
