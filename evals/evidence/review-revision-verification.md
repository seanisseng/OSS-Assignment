# Pre-inference rubric revision checks

User-supplied critique explicitly identified itself as AI-generated. Codex made
the final rubric choices under Rule A; this is not independently human-authored
or independently human-reviewed ground truth. Operator signoff remains pending.

`tests/test_scoring.py` first failed importing the intentionally absent scoring
helpers (RED); local checkpoint cab1caa preserves that test before implementation.
All five focused scoring tests then passed (GREEN): primary default, explicit
decision alternatives, alternative category bundles, irrelevant-category penalty,
and legacy single-reference behavior.

The revised rubric adds `acceptable_decisions` and `acceptable_missing_sets`.
Primary matches and alternative-accepted matches are reported separately. The
category reference is the best-F1 frozen bundle, with deterministic tie-breaking;
it is recorded per case. This avoids treating every optionally useful detail as
simultaneously required. Semantic relevance/redundancy still needs assessment.

Original report inputs and the original 50-report audit are unchanged. The
expectation hash changed before any model execution. Candidate-only searches
preserve two older blocks of 50 and body-edit metadata, without claiming those
reports were selected, fully reconstructed or included in the workload metric.

Three additional diagnostic cases are explicitly synthetic: two development,
one supplemental held-out. Their results cannot count toward the ten-real-case
held-out target. The real key still contains only one insufficient report, which
limits any claims about clarification recall or generalization.

Final verification: 23 tests passed; 96% statement coverage across contract,
publisher, runtime, clean staging and evaluation/reporting modules. Two additional
integration tests check metric counts, malformed-output accounting, absent-run
handling, and HTML escaping. Local syntax and repository checks passed.
Reproduction: `python -m unittest discover -s tests -v`,
`python -m scripts.evaluate`, and `python -m scripts.verify`.
The strict submission gate remains expected to fail while execution evidence is
absent. No inference, publication or paid usage was performed for this revision.
