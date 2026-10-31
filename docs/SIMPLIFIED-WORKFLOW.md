# Historical simplified clarification workflow: hosted smoke failed

This page is a historical record of the fourth-run configuration; it does not
describe current status. See [the experiment review](EXPERIMENT-REVIEW.md) for
the completed study and current verification commands.
The [replacement revision](SINGLE-RESPONSE-REVISION.md) was the proposed
replacement at that date and was later implemented and tested. The third hosted
smoke run reached native Auto and read the canonical skill,
but repeatedly read a large compact JSON input and delegated before GitHub
returned HTTP 429. It produced no recommendation. The proxy reported 10.36284
credits across analysis and detection; final billing remains unconfirmed.

## Proposed configuration

- `scripts/agent_input.py` exports a readable report and a source-context index.
  The original case 15051 input was about 204 KB. Its report view is under 12 KB;
  exact measured size is recorded in the pending configuration evidence.
- All approved context remains available in lossless UTF-8 chunks of at most
  8 KiB. Context filenames use trusted numeric identifiers, never report paths.
  The manifest retains the hash of the complete original frozen case.
- The same exporter is used by hosted preparation and the offline dry-run route.
  Historical inputs, answer expectations and the canonical skill are unchanged.
- Both workflow prompts assess the report first, inspect at most two relevant
  context chunks if needed, and write one structured recommendation. Unresolved
  uncertainty goes to human review; this is not a request to solve the bug.
- Copilot analysis excludes task, write_agent, read_agent, list_agents, skill,
  glob, grep and web_fetch using native CLI tool-availability flags. The skill
  is still read explicitly with cat and applied by the primary agent.
- Analysis has sixteen turns, no internal retries and a ten-minute execution
  timeout. Configured credits are twenty for analysis, five for the separate
  framework detector, and a daily setting of twenty-five. Manual dispatch bypasses that
  daily check; it is not a manual spending cap. Per-run proxy limits can overshoot
  completed responses. Framework detection retains its own runtime defaults.
- These settings supersede the initial 3+2-credit, six-turn, three-minute proposal.
  The user requested more room than the previous hosted analysis configuration
  (ten credits, eight turns, five minutes); detector credits return to five.
- Native Auto compatibility and the pinned compiler/action remain in place.
  The detector remains separate; analysis CLI tool exclusions do not configure
  its internal tools. The two-chunk reading bound is a prompt instruction,
  not a filesystem enforcement mechanism.

## Verification and approval

Tests cover lossless source reconstruction, bounded chunks including long Unicode
lines, untrusted path names, malformed context rejection, hosted and dry-run
exports, stale approval rejection, and the existing publication boundaries.
Both workflows compile with the pinned gh-aw v0.93.5 toolchain.
Run [40889513595](https://github.com/seanisseng/OSS-Assignment/actions/runs/40889513595)
tested this exact configuration on commit `eb46064`. The report and skill loaded,
and no delegation was observed. However, it read one chunk 26 times, recorded
46 turns despite the configured 16, and hit HTTP 429 without producing output.
Reported usage was 17.19639 credits across analysis and detection. The two-chunk
instruction and configured turn value are not verified enforcement mechanisms.

The prior approval belongs to its earlier configuration hash and is preserved
in review history. The user explicitly approved configuration `1a7549c8...`,
a push and one monitored 15051 smoke test with the raised limits.
`evals/evidence/simplified-configuration.json` records the proposed hash and checks.
No assistant may create a human signoff from a tooling implementation request.

Publication and smoke switches remain off. The proposed smoke preparation admits
only case 15051, main, attempt one and dispatch count four. This prepares a single
test. The recorded user approval authorizes that one dispatch, with no publication
or additional attempts. Keep all original GitHub run history.

## Limits of the evidence

Native CLI tool exclusion flags are documented in the
[Copilot CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).
Compilation verifies argument emission; the hosted trace has no delegation.
Rate-limit recovery, decision quality and actual billing remain unverified.
Restricting context inspection may increase abstentions. Fresh case evaluations
and student semantic review are still required for submission.

The updated assignment also permits a documented coding-assistant dry run using
this configuration and inputs. A hosted retry is optional, not a prerequisite
for using that route.
