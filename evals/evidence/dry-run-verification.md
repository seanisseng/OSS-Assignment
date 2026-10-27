# Dry-run tooling and conditional rubric verification

Date: 2026-10-27. These are local deterministic results, not model transcripts.
The source plan is the conversation's dry-run-first completion plan, amended by
the user's pre-inference conditions for 13902 and 13634.

## RED and GREEN evidence

- Initial new test target failed importing the absent scripts.dry_run implementation.
  Local test checkpoint: 913a4f9.
- Conditional rubric tests failed importing absent scripts.scoring helpers.
  Local test checkpoint: ed027f6.
- Standalone reproduction_detail initially received a true positive; the stricter
  test expected a false positive. The production scorer now excludes this category
  without traceback/configuration, using a rule serialized in the key.
- An altered trusted preparation was initially not checked by inspect_attempt.
  The record now binds its hash and export chronology. Test checkpoint: 607bfab.
- A startup failure initially raised JSONDecodeError instead of being archived.
  It is now retained verbatim with failed status and no invented session ID.
  Test checkpoint: ee6d175.
- Final GREEN: 44 tests passed, including the original 23 tests. No test is skipped.

## Guarantees and boundaries

| Journey | Evidence | Result |
|---|---|---|
| Export one approved case without its key/history | test_dry_run export inventory, pending/changed-review rejection | PASS |
| Preserve invalid, interrupted and pre-session failures | test_dry_run raw-byte and attempted-count checks | PASS |
| Reject altered preparation, output/skill/trace records and incomplete assessments | test_dry_run evidence checks | PASS |
| Accept complete evidence describing a failed model | test_dry_run synthetic fixture submission | PASS; fixture only |
| Reject a pending/tampered dry-run blocker | test_dry_run submission-basis checks | PASS |
| Require both 13902 reasoning checks for alternative credit | test_rubric positive/negative reasoning cases | PASS |
| Score 13634 against primary and best-F1 bundles | test_rubric specific/generic/standalone/irrelevant categories | PASS |
| Expose class imbalance | per-class tests; regenerated always-sufficient baseline 13/15 real and 9/10 held-out | PASS |
| Exclude linked discussion for 13403 | exact context inventory, original issue text and static network/tool settings | PASS; remote firewall untested |
| Separate four adversarial decisions from historical scores | test_dry_run evaluation fixture and regenerated report | PASS; no model resistance claim |

## Commands actually run

```text
python -m unittest discover -s tests -v
python -m coverage run --source=scripts.contract,scripts.publish,scripts.runtime,scripts.stage,scripts.evaluate,scripts.scoring,scripts.dry_run,scripts.evidence -m unittest discover -s tests -v
python -m coverage report -m
python -m compileall -q scripts tests
python -m scripts.evaluate
python -m scripts.verify
python -m scripts.verify --submission --mode dry-run
git diff --check
git diff --exit-code -- evals/golden/inputs evals/golden/context evals/golden/audit
```

Final coverage is 94% across 608 statements in the eight listed modules.
The tests use real temporary files and mocked GitHub calls. They ran outside the
Windows sandbox because its temporary-directory ACLs previously denied access.
Syntax and local repository verification passed. DESIGN.md has 143 lines.
No historical input, source-context or audit change appeared in the diff check.
No new Python runtime dependency was introduced; there is no project dependency
manifest to audit. No installed third-party application dependency is claimed tested.

The dry-run submission gate intentionally reports 47 missing-evidence errors:
pending complete review; missing transcript and human assessment for 22 cases;
no actual skill-loading trace; and no supported end-to-end blocker yet.
The remote gate reports 50 errors, including its four remote control records.
These are expected completeness failures, not model outcomes.

## Human review and untested controls

The user explicitly requested “AI-assisted pre-inference review, conditions open”,
not approval. review.json and freeze.json keep approval false. Their specified
scoring changes are implemented for inspection; this does not imply final signoff.
docs/REVIEW-GUIDE.md presents the nine unchanged cases and three diagnostics.
No model call, fresh assistant child, publication or repository-setting change ran.

Codex CLI 0.164.0 reports a ChatGPT login; gh was not found in this shell.
Neither fact establishes Copilot entitlement or end-to-end impossibility.
execution.json truthfully leaves that investigation pending. Hosted identity,
firewall, MCP, publication, protected-environment and phone controls remain untested.
The dry-run exporter is data isolation, not an OS-level read boundary.
