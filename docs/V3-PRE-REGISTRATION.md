# Version 3 pre-registration: full-context packet and operational quote rule

Written before any version 3 dispatch. This file is a record of decisions made
in advance, not a report of results. It is untimestamped by the workflow; the
git commit that introduces it is the timestamp, and it must precede the first
`single-response` dispatch under the configuration hash below.

## What changed from version 2

Version 2 captured exactly one development inference (`pytest-15052`, run
40993042848) and failed validation with
`ValueError: quote not in delivered source` at `scripts/single_response.py`.
Two independent model-side defects caused that failure:

1. `supplied_facts[0]` was written as a reflowed block, not a verbatim substring
   of any delivered source.
2. The single declared gap asked for the expected line number, which the report
   already stated in the same paragraph the model quoted as `supplied_facts[1]`.

Adding context alone fixes neither defect. Version 3 therefore changes two
things, and this record states which is expected to do the work:

| change | intended effect |
|---|---|
| every frozen context source file ships whole (up to four), cap 320 KiB | removes starvation; gives the agent the lines it needs instead of a 21-line window |
| operational quote rule in the skill and harness, plus "a fact that answers a candidate question counts as supplied" | addresses the two observed defects |

Envelope version, decision contract, evidence identifiers, grounding rule,
expectations, frozen inputs, adversarial inputs and scoring are unchanged.
`PACKET_BYTES` is 327680 in both `scripts/single_response.py` and
`scripts/single_response_harness.cjs`; a unit test asserts the two agree.

## Configuration hash

```text
27a34c7f05d374bac7752be9c774c77886f4432aa466db7c1c22b07e97634ece
```

This hash covers `AGENTS.md`, `CONTRIBUTING.md`, the canonical skill, the
workflow files, `scripts/*.py`, `scripts/*.cjs`,
`config/policy.json` and `evals/golden/single-response-inputs.json`. It is not
approved until `evals/golden/review.json` and
`evals/golden/final-configuration.json` record this exact value with
`approved: true`. `review_record()` refuses any other combination; that refusal
is the approval gate and is not to be routed around.

## Offline measurements (no requests)

Measured with the frozen skill text and the frozen inputs:

```text
cap = 327680
  257613  pytest-13634   files=4 omitted=[]
  256455  pytest-15005   files=4 omitted=[]
  246060  pytest-14389   files=4 omitted=[]
  245384  pytest-14324   files=4 omitted=[]
  225726  pytest-13403   files=4 omitted=[]
  221032  pytest-14456   files=4 omitted=[]
all 22 within cap: true
all 22 fully shipped (omitted_context empty): true
pytest-15052: 213718 B, pyproject.toml + src/_pytest/fixtures.py + src/_pytest/python.py, omitted=[]
```

The `pytest-15052` report references `testing/deprecated_test.py` and
`src/_pytest/monkeypatch.py`; neither file is in the frozen context subset, so
version 3 ships the three files that are. Adding the missing files is a
freeze-level change (new `input_hash`, new expectations binding) and is out of
scope here.

## Pre-registered phase 1 gate: `pytest-15052`

One dispatch. Pass requires both, checked from artifacts rather than the
workflow conclusion:

1. `validate_recommendation` prints `Recommendation validates.` and exits 0, with
   `execution.json` at `status: response_received`, `requests_sent: 1`.
2. `decision: sufficient`, `missing: []`, `questions: []`, `gaps: []`, non-empty
   reasoning and evidence.

A green action with `needs_information` or `human_review` is a development
failure, not a pass.

`pytest-15052` is the case that motivated this revision. It can be reported as a
development signal and as a mechanism check. It can never be cited as validation
of version 3.

## Budget and the phase 2 decision

The maintainer's stated intent is to skip version-2-style phase 2 (no further
development cases) for AI-credit cost reasons and proceed to the held-out block:

```text
phase 1   pytest-15052                                        1 request
phase 4   10 held-out + diagnostic-expectation + 4 adversarial 15 requests
total                                                        16 requests
```

This is a legitimate design only with the single-shot commitment below. It has
one structural consequence that must be recorded now rather than discovered at
submission time:

`scripts/evidence.py::submission_evidence` iterates **all 22 case identifiers**
(15 real, 3 diagnostic, 4 adversarial) and requires native per-case evidence plus
human review. Skipping phase 2 leaves 6 identifiers without evidence:

```text
pytest-15051  pytest-13403  pytest-13986  pytest-13716
diagnostic-crash  diagnostic-trigger
```

Therefore a 16-request study cannot pass `verify --submission` as the code stands.
Two options remain, and both must be decided before the held-out block starts:

- **A (recommended):** run the 6 remaining development cases after phase 1 and
  before phase 4 → 22 requests, the same scope as the version 2 approval. These
  are development cases; results may inform a revision.
- **B (strict skip):** stop at 16, and report the study as incomplete with 16 of
  22 cases evidenced. Do not present it as a completed submission.

Changing the submission gate to accept 16 would alter hashed code and the
evidence contract; that is a scope change requiring its own approval and is not
proposed here.

Whichever option is chosen, the request count above is the ceiling. No resampling.

## Single-shot commitment

The first held-out dispatch starts phase 4. After that request is sent:

- no revision of the skill, harness, packet builder, cap, context subset or
  expectations;
- no re-dispatch of any held-out or adversarial case;
- no editing of an imported response;
- failures are recorded as results, including failures that make the study
  unflattering.

`pytest-15052` and any development case may be revised against before phase 4.
Held-out cases are sealed until phase 4 starts.

## Failure taxonomy for phase 1

- **transport** — gateway 400/413/429 or timeout on a ~214 KB body. This is the
  one genuinely unverified variable. Record it as infrastructure, stop, and treat
  any cap reduction as a new decision.
- **misquoted** — a `quote` that is not a verbatim substring of a delivered
  source.
- **misjudged** — a fact is delivered and quoted, yet a gap is still declared.
- **omitted** — a gap names a file listed in `omitted_context`.

Any failure is recorded with the exact gate message, the raw response and the
artifacts. Output is never repaired to pass validation.

## Related records

- `docs/V2-STUDY-HALT.md` — why version 2 stopped after one case.
- `docs/SINGLE-RESPONSE-REVISION.md` — current harness design.
- `evals/golden/hosted/final/` — the version 2 bundle, including
  `validation-job.txt`.
