# Rubric revision before inference

The user supplied an AI-generated critique and delegated final judgement on the
flagged cases to Codex. This is AI-assisted review, not independent human ground
truth. No model evaluation has run and no held-out outcomes informed changes.
Operator signoff remains unrecorded; workflow operation remains disabled.

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
