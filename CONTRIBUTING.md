# AI contributions and responsibility

This is a sandbox experiment, not an upstream pytest service. Do not enable it
on other repositories. `seanisseng` owns the configuration, reviews exact drafts,
verifies billing, and is responsible for stopping it and correcting mistakes.

Disclose AI assistance in documents, code changes and bot comments. A human must
understand and verify every submitted artifact; successful execution is not proof
of decision quality. Do not label AI-written expectations as human ground truth.

Before changes: run deterministic tests, inspect the diff for secrets and verify
the frozen evaluation hashes. After model/instruction changes rerun golden tasks
in fresh isolated workspaces, preserving all failures and usage information.
Do not tune on held-out outcomes and call the same set untouched afterward.

Publication requires a maintainer's manual workflow dispatch with the hash of
the exact reviewed recommendation, matching successful analysis run and protected
environment approval if configured. Configure the environment before enabling.
Do not insert credentials into files or use a personal token for publication.

See `evals/golden/README.md` for the review and execution gates, and
`docs/OPERATIONS.md` for budget, stop and recovery instructions.

Dry-run evaluation follows `docs/DRY-RUN.md`. Never fabricate a human approval,
assessment, transcript or end-to-end blocker. A complete failed model run is valid
experiment evidence; changing its output to pass validation is not. Conditional
review is not final approval. Keep live operation disabled for the dry-run route.
