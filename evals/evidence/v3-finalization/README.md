# Version 3 evidence finalization

This package is a historical draft snapshot at its capture time, not the current
submission state; the subsequent student-signoff section below records the later
approvals. The frozen configuration remains
`27a34c7f05d374bac7752be9c774c77886f4432aa466db7c1c22b07e97634ece`.

## Checks

- `python -m scripts.evaluate --mode single-response`: regenerated hosted-only
  measurements, including failed attempts and unrun attacks. See `evaluate.txt`.
- `python -m unittest discover -s tests -v`: 89 tests passed outside the sandbox
  in 28.253 seconds. See `tests.txt`. The initial sandboxed attempt could not
  manipulate temporary directories; its failure is retained in `tests-sandbox.txt`.
  The suite also exercised pinned workflow compilation; generated runtime bytes
  and the evaluated configuration hash remained unchanged.
- `python -m scripts.verify`: local repository verification passed. Its secret
  scan covers the new artifacts. No third-party runtime packages require an
  npm/pip dependency audit; this project uses standard-library Python and Node
  built-ins. No package was installed for this finalization.
- `python -m scripts.verify --submission --mode single-response`: **failed**.
  See the exact output in `submission.txt` and status in `checks.json`. Failure
  is retained rather than bypassing the gate or fabricating missing evidence.

At this original finalization, all 22 assessments were unsigned AI drafts.
Nineteen hosted attempts have evidence; three hosted attack transcripts do not
exist. Separate six-case recovery records are not substituted into hosted paths.
Paid-overage settings remain unknown until the student supplies an actual
confirmation. The control record's configuration binding is updated, but its
billing status is not falsely promoted to tested.

## Review and controls

`shutdown.json` is a fresh read-only GitHub capture: all three launch switches
are false and no Actions run is active. The configuration-bound control record
references its exact SHA256. `controls-before-binding.json` preserves the earlier
record. Post-inference procedure review and phone cancellation remain untested.

`staged-byte-audit.json` checks that all staged hosted/recovery evidence and native
transcripts retain their worktree bytes. Git attributes disable newline conversion
for these records. Both renamed version 2 records match their previous Git blobs;
the transcript's pre-normalization Windows working copy is also retained as
`v2-transcript-working-copy.json`. Only its line endings differed from that blob.

The student should review [all 22 drafts](../../../docs/reviews/FINAL-22-CASE-REVIEW.md),
compare original inputs and responses, and provide their own reviewer identity
and actual review time when signing. No signoff is inferred from a request to
draft, verify, commit, or push evidence. Even after signoff, a hosted-only gate
cannot pass while three required hosted transcripts are missing.

The [phase 1 report](../../../docs/V3-PHASE1-RESULT.md) records the valid-but-misjudged
`pytest-15052` result, batch failures and the limits of the improved recovery
coverage. Earlier version 2 records are preserved under `v2-pytest-15052.json`.

## Provenance snapshots

`operators/` contains the trusted local operator sources used for the scoped
hosted resumptions and separate dry-run study. They are archival snapshots of
scripts originally executed from `.local/`; their root calculation assumes that
location. They are not new installed frozen-runtime code or authorization to run
another request. Native dispatch ledgers, run bindings, CLI traces, original
outputs and file inventories remain the authoritative execution evidence.

AI-use statement: Codex drafted this package and case assessments, performed the
automated checks, and preserved failures. Human semantic review is pending.

## Subsequent student signoff

All 22 case assessments, including six separate recovery interpretations, now have explicit seanisseng approvals. Current additional paid usage is user-confirmed disabled or hard-capped at $0; deductions and historical settings remain unverified. Original logs above describe the earlier draft state. See [approval receipts](../review-signoffs/) and the post-signoff verification records for the remaining hosted-only limitations.
