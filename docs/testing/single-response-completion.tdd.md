# Terminal completion correction: TDD and offline replay

AI-assisted correction of hosted run
[40920259777](https://github.com/seanisseng/OSS-Assignment/actions/runs/40920259777).
User journeys: retain the exact assessment, emit the framework's required terminal
signal without direct protected writes, and fail visibly if finalization fails.

## Failure and root cause

The agent and clean JSON-validation jobs passed. The pinned collector created
`report_incomplete` with `missing_terminal_safe_output`; the final conclusion
handler then failed. Removing the direct read-only marker write was insufficient.
Earlier tests checked the artifact path but did not exercise the collector and
conclusion handler. The original recommendation is not repaired or relabelled.

## RED and GREEN

`node --test tests/single_response.test.cjs` initially reported 13 passed and five
failed cases: the fixed completion helper was missing, success did not call it,
and completion failure was not reported. Local checkpoint: `1abe732`.

The Python mocked integration additionally demonstrated that clean validation
accepted a trace missing `terminal_safe_output`. Local checkpoint: `bdd02cd`.

After correction, all 69 Python tests pass, including 18 Node cases. The exact
commands are `python -m unittest discover -s tests -v` and
`node --test --experimental-test-coverage tests/single_response.test.cjs`.
Harness coverage is 98.28% lines, 82.69% branches. The uncovered lines are the
executable entrypoint's error wrapper. No runtime pip/npm packages were added.

| Guarantee | Evidence |
| --- | --- |
| Only a fixed trusted noop can be emitted | Node checks absolute installed CLI path, exact arguments, no shell, 15-second timeout and 16 KiB output bound |
| No direct protected-file write | EROFS regression still passes; framework service owns the write |
| Inference evidence survives completion errors | Exact raw response and recommendation retained, model/usage retained, failed trace, one provider request and no retry |
| Failed inference emits no completion | Raw transport-failure case asserts zero completion calls |
| Clean validation requires acknowledged completion | Missing terminal_safe_output is rejected; normal captured artifact validates |

## Replay of the actual saved response

`tests/replay_completion.cjs` uses the official runtime at pinned commit
`32ecafbc061c9af57e9361942099e381102ae304`. It verifies the SHA256 of the bridge,
collector and conclusion handler before execution. Supply that trusted runtime
and its bundled dependencies from the same official revision, never report code.
The runtime cache and downloaded artifacts are local diagnostics, not model inputs.

The replay uses run 7's unchanged `provider-response.json` and reconstructed
packet. The packet was built with `scripts.single_response.build_packet` from
`evals/golden/inputs/pytest-15051.json` and the canonical skill; no expectation
data is used by that builder. The executed command was:

```powershell
node tests/replay_completion.cjs .local/completion-source/runtime .local/output-fix-smoke-inspect/raw/provider-response.json .local/completion-replay-packet.json
```

The actual pinned bridge sends the fixed noop to a loopback MCP server fixture,
which records the terminal item. The actual pinned collector and conclusion
handler then run with local Actions globals. GitHub API calls are blocked; the
negative failure case attempted one diagnostic lookup, and the positive case
attempted none. No external GitHub request or new AI request is sent.

Negative result: `missing_terminal_safe_output` and `Agent reported that it could
not complete the task`. Positive result: one noop, zero collector errors, zero
conclusion errors, and the original recommendation unchanged. See
`evals/evidence/completion-replay-result.json` for source hashes and results.

This replay checks the real protocol adapter and finalization logic. It does not
exercise the hosted shell wrapper, Docker mounts, real MCP server, Actions job
orchestration or billing. It does not establish model decision quality. A new
hosted smoke requires review of the changed configuration and push/run approval.
The lifetime testing limit stays removed; there are no automatic retries.

## Primary-source references

- [Pinned CLI bridge](https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/mcp_cli_bridge.cjs)
- [Pinned collector](https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/collect_ndjson_output.cjs)
- [Pinned conclusion handler](https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/handle_agent_failure.cjs)
- [MCP CLI mounting](https://github.github.com/gh-aw/reference/tools/#mcp-cli-mounting-cli-proxy)

## Subsequent hosted verification

After explicit user approval, configuration 6b9412c7 at commit 68dda64 passed all
jobs in [run 40924362394](https://github.com/seanisseng/OSS-Assignment/actions/runs/40924362394).
The trace acknowledges the fixed noop, and the actual framework output has one
noop with no errors. This verifies the hosted wrapper/gateway and conclusion path
for one development case. It does not validate model decision quality, the full
evaluation or actual billing. See `evals/evidence/terminal-completion-smoke-result.json`.
