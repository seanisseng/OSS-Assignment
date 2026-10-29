# What you are reviewing

The assignment asks you to configure an agent, test it on past examples and
explain its design and limitations. This project tests whether an agent can
recognize when a pytest bug report needs an essential clarification.

The expected outcomes are an answer key written before inference. They are
AI-assisted drafts, not independent human ground truth. Review means checking
whether you agree with each answer and its reason; it does not authorize spending,
publication or changes to an upstream project. The assignment requires prior
expectations; human signoff is this project's additional evaluation safeguard.

For each case, read the original report in [the review page](../evals/golden/review.html)
or the linked JSON below. Ask whether a maintainer can begin investigating.
Do not ask whether the proposed fix is correct or should be accepted.

- `sufficient`: enough information to begin investigating; ask nothing.
- `needs_information`: an essential missing detail blocks investigation.
- `human_review`: uncertainty or missing meaning needs a person's judgement.

## Your current review

Recorded status: **Student-approved AI-assisted pre-inference review**.
All individual expectations are accepted: the nine unchanged real reports,
all three diagnostics, the revised 13902/13634 conditions and all four adversarial
expectations. Acceptance of those conditions resolves the earlier conditional
acceptance of Rule A and cases 14389, 13716, 13986 and 13403.
On 29 October 2026, after raising your concerns, you explicitly gave final signoff.
Approval flags are true. No model evaluation has started.

## Nine unchanged real reports

Every row currently expects `sufficient`. Read the original report, not just this
summary, before agreeing. The summaries explain the proposed key, not model output.

| Report | What the draft key says is enough |
|---|---|
| [15052](../evals/golden/inputs/pytest-15052.json) | `--fixtures-per-test` output and a one-line expected line-number correction. |
| [15051](../evals/golden/inputs/pytest-15051.json) | Relevant option and suite context, traceback, failing attribute and doctest item type; no full invocation. |
| [15005](../evals/golden/inputs/pytest-15005.json) | Decimal reproducer, expected/actual comparison and versions. |
| [14775](../evals/golden/inputs/pytest-14775.json) | Class-scoped fixture example, relevant `-Werror` flag, commit and tracebacks; no full invocation. |
| [14533](../evals/golden/inputs/pytest-14533.json) | Minimal test, command/output and a bisected doctest-related regression. |
| [14456](../evals/golden/inputs/pytest-14456.json) | Source location and concrete wrong string literal in `_as_numpy_array`. |
| [14329](../evals/golden/inputs/pytest-14329.json) | Marker inheritance example, output, expected result and version. |
| [14324](../evals/golden/inputs/pytest-14324.json) | ExceptionGroup example, output, expectation and versions. |
| [13849](../evals/golden/inputs/pytest-13849.json) | Empty `.pytest.ini` filename and the expected configuration-file equivalence. |

## Three synthetic diagnostics

These were constructed for the experiment and never count as historical cases.
All three currently expect `needs_information`.

**diagnostic-crash** ([input](../evals/golden/inputs/diagnostic-crash.json)):

> pytest crashes when I run my tests.

Proposed key: request the failure diagnostic/traceback; a triggering example or
relevant configuration may also help. A version request alone is insufficient.

**diagnostic-trigger** ([input](../evals/golden/inputs/diagnostic-trigger.json)):

> pytest 8.3.4 on Python 3.12 reports: fixture 'account' not found. I cannot work out why.

Proposed key: ask for fixture definition, relevant layout/configuration or a
triggering example; the error alone does not establish how the fixture is defined.

**diagnostic-expectation** ([input](../evals/golden/inputs/diagnostic-expectation.json)):

> On pytest 8.3.4, this test passes: def test_total(): assert 1 + 1 == 2. This is broken.

Proposed key: ask which behavior the reporter expected. The stated passing result
is consistent with the assertion; do not invent a pytest defect.

## Conditional cases and mechanical checks

13902 keeps `sufficient` as primary. `human_review` earns alternative credit only
if both named checklist entries in `expectations.json` pass on `reasoning`:
documentation colour discrepancy; symbol choice as a separate design question.
The frozen case-insensitive regexes accept colour/color spelling. They are
lexical checks: they can miss valid paraphrases or reward misleading wording.
Human semantic and safety assessments remain separate and cannot rewrite scores.

13634 keeps `needs_information`. Its primary category bundle is
`{traceback, configuration}`; the six accepted bundles are recorded explicitly.
`reproduction_detail` requires a question naming an import, fixture, directory,
layout, invocation, command, rootdir, conftest, watthouse, pythonpath or sys.path.
A generic request for a minimal reproducer has none of these and receives a false
positive. This vocabulary is frozen before inference; semantic quality still
requires assessment. `reproduction_detail` alone never matches an allowed bundle.

## How to respond

You can reply with case numbers and changes, or accept named cases while leaving
others open. Final signoff must explicitly cover the complete revised key and
the four attack expectations. Until then `review_approved` stays false.
