# Version 2 22-case study: halted after one case

Recorded `2026-10-30T17:24:10Z`. Documentation only: no inference, no approval and
no result claim follow from this record. Machine-readable companion:
[study-halt.json](../evals/golden/hosted/final/study-halt.json).

## Status

| | |
|---|---|
| Configuration | `d8b579e3e0d5434b9ef2e97f622ef90bcc82b570e99ea7e6ab806076c3ddbf4e` at `aae64a7` |
| Authorized | 22 sequential single-response requests |
| Executed | 1 (`pytest-15052`, run `41093022456`, development phase) |
| Captured | 1 provider response; recommendation validation failed |
| Not run | 21 — 20 pending bindings, 1 in progress at import; none with a captured response, transcript or execution trace |
| Study outcome | incomplete; no rate, proportion or completion claim follows from n = 1 |

The recorded request count for the whole study is 1. Absence of artifacts for the
other 21 is bounded by the collector record, not by an independent audit of
GitHub's execution state.

## Why it stopped

The single executed case failed the version 2 envelope at quote grounding:

- `supplied_facts[0]` is not a verbatim substring of delivered text — the model
  collapsed line separators, a code fence and indentation into one line;
- independently, its only gap asks for the expected line number that the report
  already states (`the 357 should be 356`), and which the model itself quoted as
  `supplied_facts[1]`.

The maintainer reviewed that failure and elected to revise the agent rather than
continue the frozen sweep. The review of this case is in progress. No further
case was executed, and none was repaired or resampled.

## What is and is not claimed

- Not a model-quality result for the configuration as a whole: one case was run.
- Not an infrastructure failure: one request, transition to `response_received`,
  trusted noop terminal record, complete native evidence. The pause record states
  `runtime_configuration_changed: false`.
- Not an approval of any revision, and not a student signoff.
- Not evidence that the other 21 cases would behave differently. They are
  unmeasured.

## Split discipline

`pytest-15052` is a development case, so observing it and then revising is within
the design of the split. The held-out cases have never been executed.

- Development (7, revisable): `pytest-15052`, `pytest-15051`, `pytest-13403`,
  `pytest-13986`, `pytest-13716`, `diagnostic-crash`, `diagnostic-trigger`.
- Held-out (10, sealed): `pytest-15005`, `pytest-14775`, `pytest-14533`,
  `pytest-14456`, `pytest-14329`, `pytest-14324`, `pytest-13849`, `pytest-13634`,
  `pytest-14389`, `pytest-13902`.

Two rules follow:

1. Do not execute the held-out cases under this configuration and then again under
   a revised one. That converts unseen evidence into tuning data; halting before
   they run is what keeps them usable.
2. `pytest-15052` is the motivating example for the revision. It may be reported as
   development evidence and as the trigger, never as validation of the revision.

The cases are **deferred, not abandoned**. Inputs, expectations, dispatch records
and the one completed bundle remain byte-identical; nothing is deleted, relabelled
or re-scored to suit the new direction.

## Authority and unspent scope

- The approval scope covered exactly 22 requests. One was consumed. The unused
  scope is not carried forward to a revised configuration.
- Any revision changes `configuration_hash`, because `AGENTS.md`, `CONTRIBUTING.md`,
  the canonical skill, `.github/workflows/*`, `scripts/*` and
  `config/policy.json` are hashed. A revised agent therefore needs a new review
  record, a new explicit approval and a new `final-configuration.json` binding;
  `review_approved` in `freeze.json` attaches to `d8b579e3…` only.
- Launch switches remain `false`; automatic resume is not authorized.
- This halt record and the accompanying documentation are outside the hashed
  configuration, so writing them does not disturb the frozen revision.

## Evidence preserved unchanged

- [Bundle](../evals/golden/hosted/final/pytest-15052/bundles/7e771010ceca42fb91158a6b1b9d38aa)
  and recovered artifacts under `evals/golden/hosted/final/pytest-15052/recovery/`.
- [Validation job log](../evals/golden/hosted/final/pytest-15052/validation-job.txt).
- [Transcript](../evals/golden/transcripts/pytest-15052.json) and
  [assessment](../evals/golden/assessments/pytest-15052.json).
- Operator records: [inspection-pause.json](../evals/golden/hosted/final/inspection-pause.json),
  [user-stop.json](../evals/golden/hosted/final/user-stop.json),
  [queue-state.json](../evals/golden/hosted/final/queue-state.json),
  [execution-summary.json](../evals/golden/execution-summary.json).

## Next steps

1. Finish the review of the executed case and record it as development evidence.
2. Revise the agent under a new configuration. Start with what the evidence
   supports: operationalise quote grounding (character-for-character substring of
   delivered text; preserve newlines and indentation; never join lines) in the
   skill and the harness instruction, not only in the JSON schema.
3. Change packet selection only if a development failure is attributable to
   omission — a gap whose `missing_fact` names a file listed in that case's
   `omitted_context`, or zero excerpts shipped while the report references source.
   Full-context dumps are not supported by the observed failure.
4. Run the seven development cases under the revision, then freeze it.
5. Run the ten held-out real reports, the remaining diagnostic and the four
   adversarial inputs only after that freeze, and regenerate reports.

Do not present the halted run as a completed evaluation, and do not resume the
frozen sweep without a separately authorized decision recorded here.
