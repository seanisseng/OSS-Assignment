# Development queue correction

The user asked to queue the remaining development cases directly in GitHub.
The first five simultaneous submissions exposed a workflow configuration bug:
its fixed concurrency group had cancel-in-progress false but omitted queue:max.
GitHub's default is one running and one pending run; new submissions replace
older pending runs. I incorrectly assumed the job discriminator made the whole
workflow group unique. It only discriminates compiler-owned job groups.

Four runs were cancelled before any jobs started: 40994834019, 40994836770,
40994840428 and 40994843772. The API verified total_jobs zero for each, so none
reached inference. The two completed tests and the already-running diagnostic
are left unchanged. Their outputs and the cancelled run records remain preserved.

The correction adds queue:max at workflow scope while retaining the fixed group
and cancel-in-progress false. GitHub can then retain the pending tests and run
them sequentially without a local dispatcher. It changes no skill, input,
model request, budget, timeout, tools or publication capability. The regression
first failed because the compiled top-level queue field was absent, then passed.
All eleven single-response Python tests pass, including the Node harness cases
and mocked execution for all seven selected cases. Repository verification passes.

The four never-started cases are submitted on the queue-fix commit. This means
results span two infrastructure configuration hashes, which must be disclosed.
The inference code and skill are byte-identical; no model answer was retried.
The batch has seven unique case inferences at most, plus four zero-job cancelled
submission records. This is not permission to rerun unsuccessful model answers.

The local collector downloads artifacts and resets the launch switch only after
all queued preparations finish. It cannot dispatch or retry inference. GitHub
runs do not depend on this computer to start. If collection is interrupted,
GitHub remains authoritative and results can be recovered later.

See evals/evidence/development-batch-20261030/cancelled-before-start.json,
operator-handoff-to-github-queue.json and batch.json for original attempts,
per-case commit/configuration and current runs.

Primary reference: [GitHub concurrency and queue:max](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
