# Offline finalization checks

The original inference code, workflows, case inputs, expectations and native
outputs are unchanged. The new tools run outside the frozen configuration hash.
This is a new verifier for the declared mixed-mode evidence, not a relaxed hosted
gate and not a claim that the agent's decisions are correct.

## TDD and verification evidence

- `red.txt`: tests first failed because review_tools did not exist.
- `initial-green-tests.txt`: 105 tests passed during implementation.
- `guard-red.txt`: new immutable-runtime and duplicate-manifest tests failed before
  the safety guards were added. Console text was converted to UTF-8; native model
  evidence was not rewritten.
- `tests.txt`: final full suite, **111 tests passed** in 29.192 seconds, including
  original pinned-compilation checks and 22 new offline regression tests.
- `coverage.txt`: **98%** coverage of review_tools, above the 80% check.
- `mixed-evidence.txt` and `report.txt`: all 22 current approvals, 19 native hosted
  attempts, six recovery sessions, two startup failures and 256 current-document
  relative links verified.
- `local-verification.txt`: original local repository check passed.

The tests ran with normal Windows temporary-directory permissions. No model,
publisher or networked agent was launched. No runtime packages were installed;
coverage was already available as a development tool.

## Finding-to-check mapping

| Audit gap | Resolution / regression target |
| --- | --- |
| Wrong pytest-13403 expectation | Corrected human_review assessment, preserved signed revision 1 and fresh revision-2 signoff; review expected-decision and stale-hash tests. |
| No combined evidence check | Closed 22-case manifest and read-only verifier; full-package offline integration test. |
| Current work absent from old commit | Final diff, staged-byte and packaged-checkout audits before the finalization commit; push requires separate approval. |
| Global approval timestamp mismatch | Earlier initial approval plus latest applicable batch/resume scopes; time/hash/commit/ceiling regression tests. |
| Stale current runbooks | One experiment map and updated current commands; local-link audit. Historical documents are labelled as history. |
| One-off recovery reproduction | Explicit-root prepare-only export, no execute option, overwrite and changed-runtime rejection tests. |
| Ambiguous performance denominators | 0/10 end-to-end and 0/2 valid held-out agreement; separate recovery and rejected-question counts. |
| Different fallback model/runtime | Comparison table and explicit unverified-control declarations; native trace/model checks and billing-attestation test. |
| Packed DESIGN prose | Normal wrapped prose, no overlong non-table lines; 150-line limit and link check. |
| Entry-point/link drift | Verifier requires the README submission entry point and resolves every relative link in the nine current documents; broken, missing and escaping-link tests. |

Original historical check logs remain under v3-finalization/ and review-signoffs/.
They describe their capture-time states; they are not overwritten to claim that
missing hosted transcripts exist. New check results record the tool source hashes.

The final packaging audit must verify that hashes still match after Git checkout,
including byte-preserved native evidence and current review receipts. See the
machine-readable validation records in this directory.

AI-use statement: Codex wrote the tools/tests and drafted these records. Actual
student approvals are separately preserved; future research remains unexecuted.
