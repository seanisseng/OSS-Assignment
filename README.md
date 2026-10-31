# Pytest bug-report clarification sandbox

Current version 3 evidence: **19/22 hosted attempts archived**, with eight valid
outputs, eight contract failures and three rate-limit failures. Three attack cases
were never dispatched. A separate six-case Codex dry run produced six valid
outputs and five expected-decision matches; it does not replace hosted failures.
See [phase 1 and batch results](docs/V3-PHASE1-RESULT.md), the
[22 draft case assessments](docs/reviews/FINAL-22-CASE-REVIEW.md), and
[recovery evidence](evals/recovery/dry-run-six-2026-10-31-v2/README.md).
Human signoff is pending and strict single-response submission verification fails.

Copilot analysis stages an essential-information recommendation; a separate
human-approved executor can post one clarification to an allowlisted sandbox issue.
Publication is disabled. The fourth hosted attempt used the smaller input and
no delegation, but looped on context reading and hit rate limiting; see
[the latest run](https://github.com/seanisseng/OSS-Assignment/actions/runs/40889513595).
The [simplified configuration](docs/SIMPLIFIED-WORKFLOW.md) did not produce a
recommendation. No further attempt of that looping version is authorized.

The [single-response replacement](docs/SINGLE-RESPONSE-REVISION.md) is implemented
and tested in GitHub Actions. [Run 40924362394](https://github.com/seanisseng/OSS-Assignment/actions/runs/40924362394)
passed every job after the trusted completion fix. See the
[completion record](docs/SINGLE-RESPONSE-AUDIT.md#hosted-completion-follow-up). Later results are linked above.
Its custom harness supplies the packet directly; the model has no investigation tools.

The updated assignment permits a documented coding-assistant dry run. Start with
[the plain-language review guide](docs/REVIEW-GUIDE.md) and
[dry-run reproduction steps](docs/DRY-RUN.md). Student review and final signoff are complete for the AI-assisted answer key.
Execution evidence is preserved; human assessments remain drafts.

Read [DESIGN.md](DESIGN.md), [evaluation instructions](evals/golden/README.md),
and [activation/stop runbook](docs/OPERATIONS.md).
Open [the local evaluation dashboard](evals/golden/dashboard.html) for current
expected/actual comparisons and baseline results.

Verify locally with `python -m unittest discover -s tests -v`,
`python -m scripts.evaluate --mode single-response` and `python -m scripts.verify`.
The strict `--submission --mode dry-run` verification must pass for a dry-run
submission. The default submission mode remains remote and requires remote
evidence. Neither mode is currently complete.
