# Rubric revision before inference

The user supplied an AI-generated critique and delegated final judgement on the
flagged cases to Codex. This is AI-assisted review, not independent human ground
truth. No model evaluation has run and no held-out outcomes informed changes.
Operator signoff is recorded below; workflow operation remains disabled.

## Subsequent user review before inference

Status: **AI-assisted pre-inference review, conditions open**, not approval.
The user accepted Rule A and cases 14389, 13716, 13986 and 13403 conditionally on
changes to 13902 and 13634. They requested the nine unchanged cases and diagnostics
before further review; docs/REVIEW-GUIDE.md presents these with original-input links.
Neither partial acceptance nor implementation of the changes authorizes inference.

On 29 October 2026, the user explicitly accepted the nine unchanged real reports
(15052, 15051, 15005, 14775, 14533, 14456, 14329, 14324 and 13849) and
diagnostic-trigger. Their expected outcomes remain unchanged. diagnostic-crash,
diagnostic-expectation, inspection of the implemented conditions, all four attack
expectations and explicit complete signoff remain open. Approval flags stay false.

Later on 29 October 2026, the user accepted all eight remaining items: both open
diagnostics, the revised 13902/13634 conditions and all four attack expectations.
This resolves the earlier conditional case acceptances. The user expressly
withheld final signoff because further concerns remain. All individual outcomes
are accepted, but approval flags remain false and inference remains blocked.

The user then specified: 13902 keeps sufficient as primary, with human_review
credit conditional on naming the docs colour discrepancy and separating symbol
choice as a design question. Both fixed regex checklists are stored in the key.
Case 13634 keeps needs_information; six explicit acceptable_missing_sets replace
loose reproduction-help wording. Primary is traceback plus configuration.
reproduction_detail is a separate category; generic reproducer requests fail its
specific-detail vocabulary check, and the category alone never matches a bundle.
Scores now report both primary and best-F1 counts, per-class results and an
always-sufficient baseline. These lexical checks have paraphrase/keyword limits;
human semantic assessment remains independent of the frozen scores.

For 13403, input.context contains the original issue and pre-report source files,
not the linked discussion; the original link/short quote remain in the issue.
Regression tests check the exact context-key inventory and workflow's empty
network allowlist/disabled GitHub tools. Hosted enforcement remains untested.
Earlier sections below describe prior revisions; the current JSON key takes
precedence over historical wording about generic reproduction-help alternatives.

## Adopted rule

Rule A: assess information sufficiency separately from whether a maintainer
accepts a requested change. A clearly specified behavior change or documentation
discrepancy can be sufficient. An unspecified intent or conflicting evidence can
still require human review. Merely using the word “feature” does not justify it.

| Case | Final expectation and reason |
|---|---|
| 14389 | Sufficient: current chaining, proposed raise-from behavior and likely location are specified. |
| 13716 | Sufficient: the syntax is in the title and desired usage-error behavior is in the one-sentence body; the proposal is investigable, not necessarily correct. |
| 13986 | Primary sufficient under Rule A; human_review also accepted for unresolved parent/subtest counting semantics. |
| 13902 | Primary sufficient for the concrete docs color discrepancy; human_review accepted if reasoning explains the mixed bug/design uncertainty. Symbol choice is a side suggestion. |
| 13634 | Keep needs_information; accept targeted traceback/configuration requests, alone or together, and concrete reproduction help combined with those diagnostics. Repeating a generic minimal-reproducer request alone is not a valid category bundle. |
| 13403 | Keep human_review: an unavailable linked discussion supplies the issue's meaning. Do not accept sufficient without that missing context. |

The other nine sufficient outcomes remain unchanged. The revised 15-real-case
key has 13 primary sufficient, one human_review and one needs_information.
The original five development cases remain intact; two synthetic diagnostic
development cases are added so clarification can be refined before held-out runs.
A third diagnostic is supplemental synthetic held-out. These do not inflate the
ten-real-case held-out denominator or pretend to improve real-case coverage.

## Scoring changes

`acceptable_decisions` records frozen alternatives. Report both primary matches
and matches against these alternatives, including for the checklist baseline.
Human relevance/redundancy assessment must inspect reasons, not just decisions.
`acceptable_missing_sets` lists alternative valid bundles of requested details.
For micro precision/recall, select the predeclared bundle with best F1 against the
prediction; ties use fewer categories, then alphabetical order. Save the chosen
reference in each result row. Do not treat a union of optional gaps as mandatory.
Unknown or irrelevant categories still produce false positives. Contract/schema
validation is unchanged; alternative rubric decisions do not loosen permissions.

## Coverage limitation and additional candidate search

The real key still has only one needs_information case. It cannot establish
reliable recall or generalization for clarification. No high score can remove
that limitation. Three labelled synthetic diagnostics exercise missing failure
output, missing triggering fixture/configuration and unclear expected behavior;
their results are reported separately from real historical results.

Two older blocks of 50 currently bug-labelled reports were fetched in creation
order, with body-edit metadata saved under `candidates/block-2` and `block-3`.
They are candidates only, not an expanded workload audit or evaluated cases.
Many apparent gaps are delegated to linked repositories, attachments or CI logs;
do not score those as absent report information without reconstructing the links.
The original 50-report workload audit and its denominator remain unchanged.
No additional historical case is claimed selected, reconstructed or reviewed.

## Final student signoff

On 29 October 2026, the user explicitly stated "ok I signoff" after accepting
all expectations and raising concerns about 15051, 14775 and 14329. The first two
rationales now describe options/context rather than claiming a full command.
Their sufficient decisions are unchanged. Case 14329 remains sufficient; intended
behaviour is for maintainers to decide after investigation. Updated expectation
and configuration hashes bind these wording corrections to the approval.
Review approval is true; evaluation has not started and live policy stays disabled.
Execution evidence and human assessments remain required before submission.
