# Final evidence-envelope revision: test evidence

User journeys were derived from the final 22-case instruction in this session.
No hosted calls were made while implementing these changes.

RED: `python -m unittest tests.test_envelope -v` ran four tests and failed with two
errors because valid version 2 envelopes were rejected as unknown/missing fields.
GREEN: the same four tests then passed after adding the closed envelope validator.
Existing tests were updated for the changed interface and full allowlist. The
final full run passed 87 tests; standalone Node passed 18 tests.

| Guarantee | Test source | Result |
|---|---|---|
| Grounded quotes, exact fields and valid references | tests/test_envelope.py | PASS |
| Every question has one gap and matching categories | tests/test_envelope.py | PASS |
| All 22 packets fit; attacks use separate frozen expectations | tests/test_hosted.py | PASS |
| Lost dispatch connections never resend inference | tests/test_hosted.py | PASS |
| Recovery downloads artifacts independently | tests/test_hosted.py | PASS |
| Missing skill, altered hashes, run reuse and incomplete evidence fail | tests/test_hosted.py | PASS |
| Complete evidence can retain a wrong model decision | tests/test_hosted.py | PASS |
| Actual review is separate from skill delivery and output structure | tests/test_hosted.py | PASS |
| One gateway request, bounded deadline and raw failure capture | tests/single_response.test.cjs | PASS |
| Legacy dry-run/publication checks remain | tests/test_dry_run.py and tests/test_integration.py | PASS |

[Full test log](../../evals/evidence/final-preflight/python-tests.txt) and
[preflight summary](../../evals/evidence/final-preflight/README.md) preserve evidence.
No coverage percentage was measured. Hosted inference, semantics, account billing
and phone cancellation were not established by local tests. Frozen code must not
be changed after final results are seen; later infrastructure changes need disclosure.
