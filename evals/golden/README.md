# Golden cases and evidence

Current results and all case links are in [the experiment review](../../docs/EXPERIMENT-REVIEW.md).
The dataset contains 15 real historical reports (five development, ten held-out),
three synthetic diagnostics and four synthetic attacks. Inputs and expectations
remain frozen. Source snapshots and MIT licences precede each report; provenance
and edit-history checks are preserved. Later comments are audit-only.

Nineteen hosted attempts are archived; three attacks have no hosted transcript.
Six separately authorised Codex recovery sessions cover three HTTP 429 failures
and those three unrun attacks. Recovery never replaces a completed hosted answer.
All 22 assessments have explicit student approval. pytest-13403's corrected review
expects human_review; its earlier signed revision remains in review-signoffs/history/.

## Current offline commands

```text
python -m review_tools verify
python -m review_tools report
python -m scripts.verify
python -m unittest discover -s tests -v
```

The new verifier validates hashes, native traces, source-linked approval scopes,
review revisions and declared control limitations. It checks hosted and recovery
modes independently, keeps invalid/absent outputs as failures, and does not pool
model accuracy. It does not launch inference or publish. Windows unit tests need
normal temporary-directory permissions; Python runtime code uses the standard library.

[Dry-run reproduction](../../docs/DRY-RUN.md) uses explicit new workspaces and
prepare-only commands. Raw hosted bundles, recovery traces and approval receipts
are retained. No output is repaired and no frozen expectation is revised to improve a score.

## Historical commands

The unchanged commands below reproduce the original hosted-only report or strict
gates. They do not validate the combined current package:

```text
python -m scripts.evaluate --mode single-response
python -m scripts.final_report
python -m scripts.verify --submission --mode single-response
python -m scripts.verify --submission --mode dry-run
```

The hosted-only gate expects all 22 hosted transcripts and a single approval time;
it cannot represent the current fallback and staged approvals. The legacy dry-run
adapter expects a different trace/prompt format. Their historical failure logs
remain evidence; use review_tools for current submission review.
The pinned compiler can still be exercised by the test suite; do not edit runtime
files, rerun collectors or rebuild frozen inputs during finalization.

Always-sufficient matches 13/15 real primary labels and 9/10 held-out; the checklist
matches 5/10 held-out. Only one real primary requires clarification. Report that
imbalance and the difference between delivery, contract validity, decision agreement
and procedural compliance. Synthetic diagnostics never count as historical inputs.
No new paid requests, secret changes or publication are authorised by these instructions.
