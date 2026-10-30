# Final study approval packet

> **Update, 2026-10-30T17:24Z:** this configuration was approved and executed for
> exactly one case, which failed recommendation validation at quote grounding. The
> 22-case study is halted after that case and the agent is under revision. No
> further case was executed. The status paragraphs below describe the
> approval-time state and are preserved as such. See
> [V2-STUDY-HALT.md](V2-STUDY-HALT.md).

Status: implemented and locally tested; final approval pending. No push or final
inference has occurred. The accepted expectations are unchanged. The previous
configuration approval does not approve these new bytes.

Configuration hash:

```text
d8b579e3e0d5434b9ef2e97f622ef90bcc82b570e99ea7e6ab806076c3ddbf4e
```

[Hashed configuration files](../evals/evidence/final-preflight/configuration-files.json)
and [frozen scope](../evals/golden/final-configuration.json) bind this request.
[Reviewable patch](../evals/evidence/final-preflight/final-revision.patch) covers the
runtime, collector, validator, tests, guides and supplied brief rename. Previous
batch evidence remains separately preserved; it is not a final-study result.

## Revision

- One tool-free Auto request per case, artifact-only; publication stays disabled.
- Version 2 envelope: grounded supplied facts, question-indexed gaps/blockers and
  the unchanged recommendation. No critic, repair request or agent loop.
- Exact provider response/assistant text plus derived artifacts; 4,096 output tokens.
- Exactly 22 allowlisted inputs; separate adversarial expectation handling.
- One-shot ledger, token/run/commit binding, independent recovery and native hosted
  import. Refusals, malformed output and failures are retained.
- Evidence completeness, response validity, decision agreement and actual case review
  are distinct. Legacy evidence modes retain their requirements.

## Requested authorization

Approve these frozen bytes for a local inference commit, one push of that commit,
and the sequential 22-request evaluation. Use the same commit/hash for all cases.
After approval, record its actual timestamp, update the configuration approval
record, commit/push and bind the collector plan to that SHA. A commit cannot contain
its own SHA; the ledger/run records and later submission commit will record it.
No runtime changes follow this freeze.

Run five real development reports and two development diagnostics first, followed
by ten held-out real reports, the remaining diagnostic and four adversarial inputs,
including fake maintainer approval. Exact order is in the frozen scope above.
Archive each case before the next. Continue after model/schema mismatches; pause
on infrastructure, authentication or throttling. Connection loss permits artifact
recovery only, never another inference. Additional calls need explicit approval.

The per-run proxy ceiling is five credits, 110 summed across 22 planned calls.
This is an estimate ceiling, not a prediction or guarantee of account deductions.
Check account usage and paid-overage-disabled status before starting; capture
available usage after completion/interruption. Keep the launch switch false until
approved execution, then clear it after completion/interruption. Hard termination
can interrupt cleanup and evidence finalization; independently confirm state.

## Validation and remaining work

See [preflight evidence](../evals/evidence/final-preflight/README.md) for actual
commands/results and packet sizes. Compilation used gh-aw v0.93.5. The lock was
inspected for read-only analysis, Auto, no detection request, pinned actions,
full packet upload, ten-minute execution and five-credit proxy configuration.
Under the version 2 configuration, all 22 packets fit 32 KiB; largest was 23250 bytes.
That bound is superseded: the current packet builder ships whole files under a
320 KiB allowance, and all 22 packets were re-measured below that bound.

The submission gate intentionally fails today: final approval, 22 native bundles,
actual case assessments and final account/control evidence do not exist. No outputs
or human review timestamps are fabricated to fill those locations.

After execution: regenerate reports, review each case, update findings/control
statuses, run the strict single-response gate and credential/cache checks. Present
the exact submission diff/commit for approval before its push. Then deliver that
GitHub commit URL for eLearn. The repository is public; ctreude access is unnecessary
while visibility remains public.
