# Single-response output failure: TDD evidence

Derived from hosted run [40917225932](https://github.com/seanisseng/OSS-Assignment/actions/runs/40917225932)
and the user's request to fix it. AI-assisted implementation and documentation.

User journeys: preserve a successful model response without writing protected
framework files; give the model an unambiguous output contract; reject malformed
responses without repair; permit repeated manually approved tests without a lifetime counter.

## Reproduced failures

`node --test tests/single_response.test.cjs`: 13 passed, 2 failed before the fix.
The new schema test failed because no explicit JSON contract was supplied.
The read-only-path test raised `EROFS` after inference, reproducing the hosted bug.
Checkpoint: `20611e3`. Tests use a mock transport; no inference is performed.

The mocked preparation/validation test then failed with
`single-response smoke attempt exhausted or unknown` at total_count three,
before changing the old two-dispatch guard. Checkpoint: `9e70ccb`.

## Guarantees and validation

| Guarantee | Test | Evidence |
| --- | --- | --- |
| Successful response capture never writes framework safe outputs | Node read-only-path regression | EROFS injected on protected writes; one mocked request, response and trace retained |
| Prompt specifies evidence as source-key strings | Node request contract regression | Closed schema, bound case ID/hash and permitted identifiers checked |
| Python and prompt agree on fields and missing categories | Python mocked preparation/clean-validation integration | Compares schema with authoritative FIELDS/CATEGORIES; validates ZIP-extracted artifact |
| Object-shaped evidence remains invalid | Python no-repair validation test | ValueError; historical response is not coerced or rewritten |
| Repeated manual tests need no lifetime-counter reset | Python mocked preparation integration | No workflow-count API calls; run attempts 1, 2 and 17 prepare with other gates preserved |

GREEN commands: `python -m unittest discover -s tests -v` (69 tests, including the
15 Node cases); `node --test --experimental-test-coverage tests/single_response.test.cjs`
(15 passed; harness line coverage 98.10%, branch coverage 83.67%);
`python -m scripts.evaluate`; `python -m scripts.verify`.

The full suite also recompiles the pinned workflows. Held-out evaluation has
zero attempts; deterministic test success is not measured model decision accuracy.
No new hosted test or push is included. No runtime pip/npm dependencies were added.
The remaining uncovered Node lines are the executable entrypoint's error wrapper.

## Limits and follow-up

The schema is prompt guidance; the provider may still return invalid JSON or a
poor decision. Keep strict Python validation and human semantic review. The
read-only test simulates EROFS; only a new approved hosted run can verify the
complete success path. Evidence for the sixth run remains unchanged in GitHub
and `evals/evidence/hardened-single-response-result.json`.

Configuration approval is pending for the changed tree; the launch switch stays
off. The user explicitly requested removal of the local lifetime testing limit.
A new no-count-query regression failed before removing it (checkpoint `b3b62c7`).
Local checkpoints preserve RED/GREEN evidence; do not push without approval.
