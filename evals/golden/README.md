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
One hosted smoke attempt failed before a model response; its native Copilot trace
remains in GitHub Actions history; local debug copies were removed on request. No recommendation or human assessment exists.

```text
python -m unittest discover -s tests -v
python -m scripts.evaluate
python -m scripts.verify
python -m scripts.verify --submission --mode dry-run
```

The strict command must fail until the outstanding execution evidence exists.
Default submission mode is remote; it also requires populated remote evidence.
Windows tests need an unrestricted shell because sandbox temporary-directory ACLs
deny access. Runtime code needs only Python 3.12 standard-library modules.

Follow [the dry-run guide](../../docs/DRY-RUN.md). Helpers export one case outside
the repository and import exact output and real Codex JSONL events. The adapter
does not enforce all hosted controls; document every untested control and the actual
end-to-end blocker. Unknown entitlement alone is not evidence of impossibility.

Each attempt retains actual/CASE_ID.json when output exists, transcripts/CASE_ID.json,
transcripts/raw/CASE_ID.jsonl, trusted preparations/CASE_ID.json and a student-written
assessments/CASE_ID.json. No output on an interruption is recorded as a failure,
not a no-action result. Never repair invalid JSON or overwrite an earlier attempt.
Completed runs need actual skill-read events and matching content, not self-report.

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
