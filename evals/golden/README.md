# Reproduction and evidence status

The historical inputs are original public pytest reports with zero recorded body
edits, checked via audit/edit-provenance.json. context/NUMBER/ preserves source and
MIT license at a revision no later than each report; provenance.json records it.
Later comments and edit history are evaluation-only and never exported to the model.

The key contains five real development and ten real held-out cases, three separate
synthetic diagnostics and four separately scored attacks: 22 inputs in total.
Only one real case needs clarification. Synthetic diagnostics do not improve the
real sample's coverage or count toward historical denominators.

Current review is **Student-approved AI-assisted pre-inference review**.
The user accepted all individual expectations, including Rule A, the revised
13902/13634 conditions, all diagnostics and all four adversarial expectations.
Final signoff was explicitly given on 29 October 2026; review approval is true.
See [the review guide](../../docs/REVIEW-GUIDE.md), review.json and REVIEW-REVISION.md.
The earlier development batch completed seven workflows: 1/5 real and 2/2 diagnostic
decision matches. Its preserved bundles are separate from the final configuration.
The final study awaits approval of the tested diff, configuration hash and 22 calls.
Accepted expectations and historical inputs remain unchanged.

```text
python -m unittest discover -s tests -v
node --test tests/single_response.test.cjs
python -m scripts.compile_workflows
python -m scripts.evaluate --mode single-response
python -m scripts.final_report
python -m scripts.verify
python -m scripts.verify --submission --mode single-response
```

The strict command must fail before complete execution evidence and actual reviews
exist. Wrong model decisions may remain. Windows tests need an unrestricted shell
because sandbox temporary-directory ACLs deny access. Runtime Python uses only the
standard library. The Node harness uses built-ins; compiler/actions are pinned.

The final hosted mode checks native request, canonical skill, bounded packet,
provider response, assistant text, derived files, commit and unique run provenance.
It does not fabricate Codex events. `hosted/` preserves original downloaded bundles;
`actual/` holds structurally valid extracted recommendations, `transcripts/` holds
native provenance records and `assessments/` holds explicitly draft/reviewed case
assessments. Invalid output stays in original bundles and transcripts as a failure.
The model's evidence audit is stored in the bundle and draft assessment. It does
not establish procedural compliance. Complete evidence is distinct from correctness.

See [operations](../../docs/OPERATIONS.md) for ledger/recovery commands. Record before
dispatch, recover by token/run ID, and never infer that a lost connection permits
another request. Refusals and cancellations remain visible. Run one case at a time
on the approved frozen inference commit. Clear the switch after completion or stop.
Legacy [dry-run](../../docs/DRY-RUN.md) checks still require actual Codex tool events;
legacy remote submission still checks publication and phone-stop evidence. The new
artifact-only mode instead requires accurate control-status explanations.

Reporting separates primary and conditional decision matches, per-class results,
and primary/best-F1 missing-category counts. The primary 13634 bundle is traceback
and configuration. Acceptable bundles and regex checks are frozen in expectations.
The always-sufficient baseline matches 13/15 real primaries (9/10 held-out), while
the checklist matches 5/10 held-out. Report these class-imbalance limits honestly.
Attack decisions are separate; tool behavior and safety need human assessment.

Do not rerun collectors or scripts.freeze to improve scores. Freeze refuses to
overwrite an approved or executed study. Changes after held-out inference require
a separately versioned study. Preserve original raw inputs and every failure.
Archive remote artifacts before expiry and never save credentials in evidence.
