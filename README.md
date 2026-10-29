# Pytest bug-report clarification sandbox

Copilot analysis stages an essential-information recommendation; a separate
human-approved executor can post one clarification to an allowlisted sandbox issue.
Publication is disabled. The third hosted attempt reached native Auto and loaded
the skill, but hit rate limiting before producing a recommendation; see
[the latest run](https://github.com/seanisseng/OSS-Assignment/actions/runs/40827503414).
The [simplified configuration](docs/SIMPLIFIED-WORKFLOW.md) is locally tested and
approved for one monitored hosted smoke test with raised limits.

The updated assignment permits a documented coding-assistant dry run. Start with
[the plain-language review guide](docs/REVIEW-GUIDE.md) and
[dry-run reproduction steps](docs/DRY-RUN.md). Student review and final signoff are complete for the AI-assisted answer key.
Execution evidence and human assessments are still pending.

Read [DESIGN.md](DESIGN.md), [evaluation instructions](evals/golden/README.md),
and [activation/stop runbook](docs/OPERATIONS.md).
Open [the local evaluation dashboard](evals/golden/dashboard.html) for current
expected/actual comparisons and baseline results.

Verify locally with `python -m unittest discover -s tests -v`,
`python -m scripts.evaluate` and `python -m scripts.verify`.
The strict `--submission --mode dry-run` verification must pass for a dry-run
submission. The default submission mode remains remote and requires remote
evidence. Neither mode is currently complete.
