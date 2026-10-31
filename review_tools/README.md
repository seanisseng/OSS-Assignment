# Offline evidence tools, version 1

These tools are deliberately outside `scripts/`, whose bytes are part of the
historical inference configuration. They make no provider or GitHub requests.
Node is used only to reconstruct the hash-checked frozen request template.

```text
python -m review_tools verify
python -m review_tools report
python -m review_tools --root PATH_TO_REPOSITORY verify
python -m review_tools replay --case fake-approval --workspace NEW_OUTSIDE_DIRECTORY --prepare-only
```

`verify` is read-only and exits 1 for missing, changed, unapproved or inconsistent
evidence. It also requires the README submission entry point and resolves every
relative link in the current documents. `report` writes the experiment map,
machine-readable report and per-case review index; it also exits 1 when the
package fails. Model mistakes do not by themselves fail an evidence audit when
preserved, explained and reviewed.

`replay` only prepares files. There is no execute command or automatic retry.
It rejects changed runtime bytes before invoking Node, existing destinations,
repository-internal destinations and cases outside the six-case recovery scope.

## Manifest and trust

`evals/evidence/v3-evidence-manifest.json` is the versioned, closed-field declaration
of all 22 cases, their hosted dispositions, six recovery paths and current approval
receipts. It explicitly selects pytest-13403 revision 2; revision 1 remains history.
Source-linked dispatch approvals are checked by case, time, hash, commit and ceiling,
using the latest applicable scoped event. Refused/unrun/incorrect outcomes are not
relabeled successes. The original hosted-only gate is retained unchanged.

Raw native bundles and signed assessments require byte-for-byte SHA256 matches.
Original input JSON is independently bound by the frozen object digest. Older
review receipts hashed Windows JSON-file whitespace; their raw input SHA256 may
match either LF or CRLF serialization, without changing field values or receipts.
Approval-source JSON uses `scripts.contract.digest` over parsed JSON to avoid
serialization-only differences. Duplicate manifest keys and unknown fields fail.

Hashes support integrity, not proof that a forged operator record is authentic.
The user-attested billing cap is not an independently tested enforcement control.
Zero observed recovery tool actions do not prove hosted isolation or public safety.
Recovery model/runtime differences and native finite-retry uncertainty remain disclosed.

## Regression coverage

Run `python -m unittest discover -s tests -v`. The added tests cover approval scope,
chronology, revision hashes, Windows serialization, trace/session/final-message
bindings, tool actions, native CLI parsing, metric denominators and prepare-only
replay. [Captured checks](../evals/evidence/review-tools/README.md) include RED/GREEN
evidence, the full-suite result, coverage and packaged-checkout verification.
