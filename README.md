# Pytest bug-report clarification sandbox

Copilot analysis stages an essential-information recommendation; a separate
human-approved executor can post one clarification to an allowlisted sandbox issue.
Publication is disabled. The fourth hosted attempt used the smaller input and
no delegation, but looped on context reading and hit rate limiting; see
[the latest run](https://github.com/seanisseng/OSS-Assignment/actions/runs/40889513595).
The [simplified configuration](docs/SIMPLIFIED-WORKFLOW.md) did not produce a
recommendation. No further attempt of that looping version is authorized.

The [single-response replacement](docs/SINGLE-RESPONSE-REVISION.md) is implemented
and locally tested. Its second smoke returned a recommendation, then failed writing
a protected marker; the recommendation also violated the output contract. The
[local corrections](docs/SINGLE-RESPONSE-AUDIT.md#second-smoke-response-capture-and-output-contract) await approval before push or another run.
Its custom harness supplies the packet directly; the model has no investigation tools.

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
