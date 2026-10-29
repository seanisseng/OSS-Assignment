# Native Copilot Student automatic selection candidate

The first smoke run used model: auto, but gh-aw v0.93.5 resolved that framework
alias to claude-sonnet-5.5. Copilot rejected the concrete selection as unsupported.
The account's native automatic model selection should be left to Copilot.

The user-authorized replacement adds the following under engine, preserving the existing
model: auto metadata, prompt, skill and other controls:

```yaml
env:
  COPILOT_MODEL: ""
```

The compiler's final engine environment merge emits an empty COPILOT_MODEL in
both analysis and detection. Neither invocation contains a --model flag. Inspection
of the exact pinned copilot_harness.cjs shows that alias resolution returns early
when COPILOT_MODEL is empty. This is a supported environment configuration,
not a modification of the upstream harness or an access-policy bypass.

Configuration: .github/workflows/smoke.md and its compiled lock.
Static verification: evals/evidence/student-auto-preview.json.
The limits remain ten analysis credits, five detection credits and fifteen daily;
network isolation, integration identity and publication restrictions are preserved.

Compilation proves the runtime override is unset, not that hosted inference will
succeed. Native Copilot defaults and the API proxy still need a real test. The
separate MCP protocol error observed in the first attempt may also remain.

The user approved one replacement attempt. Its preparation accepts only the
second workflow dispatch and rejects reruns or a third dispatch. The reviewed
answer key is unchanged. First-run debug downloads were removed on request;
GitHub retains the original run history.

References:
- https://docs.github.com/en/copilot/get-started/plans
- https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/copilot_harness.cjs
- https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/pkg/workflow/copilot_engine_execution.go
