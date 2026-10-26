# Pytest bug-report clarification sandbox

Copilot analysis stages an essential-information recommendation; a separate
human-approved executor can post one clarification to an allowlisted sandbox issue.
Operation is disabled by default. No inference or publication has run yet.

Read [DESIGN.md](DESIGN.md), [evaluation instructions](evals/golden/README.md),
and [activation/stop runbook](docs/OPERATIONS.md).
Open [the local evaluation dashboard](evals/golden/dashboard.html) for current
expected/actual comparisons and baseline results.

Verify locally with `python -m unittest discover -s tests -v`,
`python -m scripts.evaluate` and `python -m scripts.verify`.
The strict `--submission` verification must pass before submitting a commit URL.
