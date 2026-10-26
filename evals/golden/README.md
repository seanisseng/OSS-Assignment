# Reproduction and evidence status

Inputs are original public pytest reports with zero recorded body edits, checked
via `audit/edit-provenance.json`. No later responses enter their context maps.
`context/NUMBER/` preserves source files and MIT license at a commit no later than
the report creation cutoff; `provenance.json` identifies the revision and URL.
The subset is data for inspection, not code to execute.

`expectations.json` was authored with AI assistance before model execution.
There are five development cases, ten held-out cases (nine no-action), and four
synthetic injection cases in `adversarial/`. Student review has been requested.
`freeze.json` records expectation hash and pending approval/execution status.
Do not change frozen expectations after looking at held-out model outputs.

Run from the repository root:

```text
python -m unittest discover -s tests -v
python -m scripts.evaluate
python -m scripts.verify
python -m scripts.verify --submission
```

The final command intentionally fails while required evidence is absent.
On this Windows sandbox integration tests require escalation because Python's
temporary-directory ACLs deny sandbox access. They pass outside the sandbox.
No third-party runtime Python dependencies are needed; coverage is optional.

Read `docs/OPERATIONS.md` before enabling anything. Collectors make read-only
GitHub requests, use existing Git credentials in memory and never print/save
them. `python -m scripts.collect` refreshes the sample; do not use it to mutate
frozen evidence without creating a separately versioned study.
`python -m scripts.research_context` checks edit histories and preserves prior
source. `python -m scripts.freeze` rebuilds draft expectations; do not rerun after
student approval or substantive model execution. Both operations change hashes.

For each executed case retain:

- `actual/CASE_ID.json`: exact model JSON, no manual repair.
- `transcripts/CASE_ID.json`: real transcript/tool calls, run URL, timestamps,
  reported engine/model, usage where available, config hash and skill-read evidence.
- `assessments/CASE_ID.json`: student relevance/redundancy assessment and any
  disagreement explanation. Never silently omit failed or interrupted runs.

Currently these folders contain only status README files. No model transcript
or actual output has been invented. The dashboard and report show “not run”.
The baseline is intentionally a simple presence checklist (fenced code,
pytest version/commit and behaviour keywords); it is not the proposed agent.
Precision/recall are micro-averaged over missing categories; zero denominators
are null. Validation failures count as incorrect attempted decisions, and absent
runs are reported separately. Semantic assessments require human judgement.

Before publication copy actual setup hash and tool-trace evidence into the run
record. File existence or an agent assertion that it loaded the skill is not proof.
Archive expiring GitHub artifacts locally; leave secrets out of transcripts.
