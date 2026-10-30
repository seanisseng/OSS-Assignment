# Local monitor interruption and recovery

The first selected run, 40993042848 (pytest-15052), completed successfully in
GitHub Actions. The local launcher stopped because a gh run view status read
returned exit code 1. Its captured state does not identify a more specific cause;
this is not evidence of a Copilot rate limit or inference failure.

The original stopped state is preserved in operator-interruption-1.json. On the
user's return, the operator recovered that existing run's artifacts and resumed
only the six cases that had never been dispatched. The first case was not rerun.

The local monitor now permits up to three attempts for read-only API/status
queries, with ten seconds between attempts. Dispatch, switch changes and model
inference are not automatically retried. The GitHub workflow and approved
configuration are unchanged. Both launch switches were off when recovery began.

The batch remains incomplete until batch.json reports all seven cases completed.
Human quality assessments remain pending even when workflow jobs succeed.
