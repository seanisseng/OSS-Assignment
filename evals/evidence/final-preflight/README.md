# Final revision preflight evidence

This is local pre-inference evidence, not a claim of hosted model performance.
Configuration and call scope are in [the approval packet](../../../docs/FINAL-STUDY.md).

| Check actually run | Result |
|---|---|
| `python -m unittest discover -s tests -v` | 87 tests passed; [UTF-8 log](python-tests.txt). Includes Node transport suite. |
| `node --test tests/single_response.test.cjs` | 18 tests passed, zero failed, cancelled or skipped. Standalone execution observed in this session. |
| `python -m scripts.compile_workflows` | gh-aw v0.93.5: clarify, smoke and single-response compiled; zero warnings. |
| Generated lock inspection | Full 22 choices, dispatch token, read-only analysis, Auto, no detection job, pinned actions, complete packet upload, ten-minute execution step, five-credit proxy ceiling. |
| `python -m scripts.verify` | Passed repository structure, frozen-input checks and configured secret scan. |
| `git diff --check` | Passed. Windows warns about eventual CRLF in .gitattributes; hashed runtime files are LF. |
| `python -m scripts.verify --submission --mode single-response` | Expected failure: new approval, 22 run bundles, case reviews and final control/account evidence are absent. |
| All 22 packets | 6,817?23,250 bytes, all below 32,768; [per-case sizes](packet-sizes.json). |
| Read-only GitHub state | Public repository; launch variable false; [observation](repository-state.json). |

The Python tests cover exact envelope fields, bounds, quote grounding, references,
question/category correspondence, duplicate JSON keys, all frozen inputs, explicit
adversarial handling, dispatch-before-send, connection recovery without redispatch,
unique run IDs/commit binding, absent skill delivery, tampered hashes, incomplete
execution, malformed output preservation, draft review rejection and legacy modes.
They also establish that reviewed wrong decisions can have complete native evidence.
These mocked tests do not establish hosted semantic quality or actual account cost.

[Configuration file hashes](configuration-files.json) bind the runtime and workflow
bytes. [Reviewable patch](final-revision.patch) includes new implementation files;
previous batch files are preserved separately and were not rewritten in this task.
The supplied brief rename remains under its current canonical filename. No runtime
pip/npm packages were added. Coverage percentage was not measured or claimed.

After approval, inspect available account usage and paid-overage settings before
any inference. Record real results, reviews and controls rather than changing this
preflight record into a claim that the final experiment has already happened.
