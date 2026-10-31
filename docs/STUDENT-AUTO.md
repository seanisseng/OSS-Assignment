# Native Copilot Auto compatibility correction

Historical compatibility proposal; the hosted result below supersedes its initial status.
For all three failures see [HOSTED-ACTION-ISSUES.md](HOSTED-ACTION-ISSUES.md).
Historical configuration at that attempt: [SIMPLIFIED-WORKFLOW.md](SIMPLIFIED-WORKFLOW.md).
Current status and results are in [the experiment review](EXPERIMENT-REVIEW.md).

## What changes

The first attempt's model: auto was resolved by gh-aw to a concrete model, which
Copilot rejected. The second attempt cleared COPILOT_MODEL, but the proxy-backed
CLI requires an explicit selector. Neither attempt produced a recommendation.
Their original GitHub run history remains; local first-run debug downloads were
removed at the user's request.

Both analysis workflows now explicitly request auto. Before the analysis and
threat-detection CLI runs, a trusted step verifies the exact SHA256 of the pinned
Copilot launcher and adds preserveAuto for that exact selector to its existing
shared resolver call. Other model identifiers are unchanged. The resolver already
supports this option; the correction supplies it at the missing call site.

The result is an explicit auto selector for the CLI, passed through to Copilot
rather than rewritten to a concrete model by the launcher. No model entitlement,
credential, provider identity or upstream access rule is changed. The AWF proxy
stays enabled with its network and credit controls. Its pinned specification
supports conservative credit accounting for the dynamic copilot:auto selector.
A model selection is not a confirmed successful inference until a real run shows it.

## Reproducible build

Run python -m scripts.compile_workflows with the reviewed gh-aw v0.93.5 compiler.
The wrapper first runs the official release compiler with the existing immutable
action SHA, then adds the compatibility step to both runtime jobs in each lock.
The compiled metadata still corresponds to the Markdown inputs. This additional
build step is intentional; direct gh aw compile alone removes the correction.

The launcher source SHA256 is fixed in scripts/compile_workflows.py. Unknown,
already-modified or structurally ambiguous launchers are refused before writing.
The analysis CLI is skipped on failure; the detector explicitly requires its
compatibility step to succeed. Upgrading the compiler/action requires reviewing
and updating this correction rather than silently patching unfamiliar code.

## Controls and validation

- Ten configured analysis credits, five detection credits, fifteen rolling daily.
- Network isolation, staged outputs, the canonical skill and prompt retained.
- Internal harness retries set to zero; no repeated startup attempts.
- Publication policy remains disabled and publisher rejects smoke artifacts.
- Local smoke preparation allows only dispatch count three for case 15051, main,
  the sandbox repository and GitHub run_attempt one. A fourth dispatch is refused.
- New runtime configuration approval is pending; preparation refuses inference
  until the human approves its configuration hash. Case expectations are unchanged.

The suite checks exact-source hashing, single-site modification, unknown-version
rejection, both runtime jobs, preserved detection conditions and fail-closed guards.
The generated Python correction was replayed against the exact pinned launcher
bytes; only the preserveAuto option changed. Node syntax validation passed without
executing the launcher. No reporter or historical pytest code was executed.

Hosted native-Auto/provider compatibility and the previously observed MCP protocol
warning remain unverified. Do not describe local tests as successful agent evaluation.
The next useful test is one separately authorized 15051 smoke attempt under the
same credit limits. No further inference has been performed.

## Primary references

- https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/resolve_model_alias.cjs
- https://github.com/github/gh-aw/blob/32ecafbc061c9af57e9361942099e381102ae304/actions/setup/js/copilot_harness.cjs
- https://github.com/github/gh-aw-firewall/blob/v0.28.70/docs/awf-config-spec.md

## Hosted verification result

Run 40827503414 completed with failure. Native Auto reached the provider and the
canonical skill was actually read. The model delegated and repeatedly tried to
read/search the large compact case JSON, then hit GitHub rate limiting. No
recommendation file exists, so this is not a successful end-to-end evaluation.
Proxy-reported usage was 10.08027 analysis credits and 0.28257 detection credits;
final account billing is unconfirmed. The detector also hit rate limiting.
The smoke switch is off, publication stayed disabled and no further run started.
Temporary debug downloads were removed after inspection; GitHub retains the logs.
