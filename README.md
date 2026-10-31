# Pytest bug-report clarification experiment

Start with **[the experiment review and submission map](docs/EXPERIMENT-REVIEW.md)**.
It links all 22 cases, expected/actual outcomes, signed assessments and evidence.
[DESIGN.md](DESIGN.md) gives the design justification, governance, model bill of
materials and five required answers within the assignment's 150-line limit.

The hosted study attempted 19/22 cases: eight valid outputs, eight contract
failures and three HTTP 429 failures. Three attacks were not dispatched.
A separately authorised six-case Codex recovery produced six valid outputs and
five decision matches. These results are not pooled or substituted for hosted failures.
All 22 assessments are signed; pytest-13403 has a corrected, freshly approved
revision, with its earlier mistaken assessment and approval preserved as history.

## Verify and reproduce

Run these offline checks from the repository root:

```text
python -m review_tools verify
python -m review_tools report
python -m scripts.verify
python -m unittest discover -s tests -v
```

The new evidence audit checks the declared mixed-mode package and scoped approval
history. A pass establishes consistent evidence, not successful agent decisions
or a guaranteed grade. Windows tests need normal temporary-directory permissions.
[Preparation-only reproduction](docs/DRY-RUN.md) never launches an assistant.

The original hosted-only and legacy dry-run gates remain in the frozen scripts
for historical reproduction. They are not the current mixed-mode audit and are
not relaxed to manufacture missing transcripts. [Operations](docs/OPERATIONS.md)
separates current review steps from historical capture procedures.

The assignment permits a documented coding-assistant fallback. Recovery retained
frozen inputs and procedure but changed model/runtime; hosted safeguards remain
unverified for those cases. Publication and launch switches remain disabled.
The tested agent does not justify deployment; [future research](docs/FUTURE-STUDY.md)
is a proposal only and authorises no new calls.

Historical evidence remains under [earlier development](evals/evidence/development-batch-20261030/),
[hosted version 3](evals/golden/hosted/v3/) and [separate recovery](evals/recovery/dry-run-six-2026-10-31-v2/README.md).
Submit the specific final commit you approve; local changes are not part of an older commit URL.
