# Local verification evidence

Execution date: 2026-10-27 (Asia/Singapore).
This record describes actual local checks. It is not an inference transcript.

## TDD and deterministic checks

RED: `python -m unittest discover -s tests -v` failed on the intentionally absent
`scripts.contract` implementation. Checkpoint: dd98016.
GREEN: the contract implementation passed all six initial tests.
Expanded suite: 16 tests passed; 95% statement coverage across contract, publisher,
runtime and clean staging modules. Coverage: contract 100%, publisher 97%,
runtime 88%, stage 94%. Optional coverage.py version 7.16.2 was already installed.

Command:
`python -m coverage run --source=scripts.contract,scripts.publish,scripts.runtime,scripts.stage -m unittest discover -s tests -v`
Then `python -m coverage report -m`.

Windows first denied access to temporary directories inside the sandbox.
An unrestricted retry exposed a cleanup-order fixture bug (deleting the active
working directory). Cleanup was corrected to restore cwd first. The final suite
passed outside the sandbox. These failures were test-environment/fixture errors,
not recorded as model or executor safety failures.

Tested properties include unknown keys/decisions/categories, wrong field types,
unresolvable evidence, no-action silence, comment/question bounds, foreign and
unallowlisted targets, exact-hash approval, stale/duplicate publication, daily
limit, disabled operation, cancelled analysis, missing input, pagination safety,
clean-job validation, all four prohibited-action payloads and a 300-request burst.
The mocked POST checks the exact fixed endpoint, method, AI notice and run link.
It never calls GitHub. Model responses to the four attacks remain untested.

## Compiler and repository checks

Official gh-aw v0.93.5 compiled `clarify.md` successfully. Initial compilation
failed on unresolved setup action pins; the official release tag was resolved
through the API to 32ecafbc061c9af57e9361942099e381102ae304 and used explicitly.
Compiler-release metadata is preserved in compiler-release.json.
Inspection found default failure-reporting issue-write scopes. Reporting options
were disabled/staged and recompilation removed all analysis write scopes.
The GitHub MCP toolset was explicitly disabled; safeoutputs is the only MCP.

`python -m compileall -q scripts tests`: passed.
`python -m scripts.verify`: passed (required files, <=150 DESIGN lines, frozen
input/expectation/context hashes, pinned action references, no analysis write
scope, Python syntax and targeted credential patterns).
`python -m scripts.evaluate`: reproduced baseline 5/10; model metrics are null.
`python -m scripts.verify --submission`: correctly failed due to absent student
review, all 19 actual outputs/transcripts and four remote evidence records.

No runtime package dependencies were added, so a dependency-vulnerability audit
has no installed project dependency graph to inspect. ruff is not installed;
syntax and deterministic checks were used rather than claiming a clean ruff run.

## Historical collection and remaining gaps

50 public bug-labelled pytest reports collected with raw comments/events.
Collection first hit the public API limit after 28 records. Resuming with existing
Git credentials completed it; credentials stayed in memory, without value logging.
GraphQL edit metadata identifies 33 unedited candidates. Fifteen were selected
and frozen with source context and license from pre-report revisions.
41/50 had another detected non-bot response; median 45.5189 hours among responders.
Nine unresolved reports retain null response times. Draft clarification count
3/50 needs full student review; assistant excerpt coding was not exhaustive.

No model run, publication, account entitlement check, paid usage, actual
skill-loading trace or phone-only stop rehearsal is claimed. Workflow activation
is disabled, targets are empty and allowance is unverified. Remote settings and
environment protection have not been modified. Nothing has been pushed.
