# Prepare-only recovery reproduction

The current recovery is the [separate six-case study](../evals/recovery/dry-run-six-2026-10-31-v2/README.md).
It covers pytest-14533, pytest-14456, fake-approval, impersonation, malicious-tool
and secret-exfiltration. Three hosted HTTP 429 failures and three unrun cases
remain recorded as such. Frozen expectations and original responses are unchanged.

## Verify existing evidence

```text
python -m review_tools verify
python -m review_tools report
```

The checker reconstructs the frozen canonical messages, checks packet/skill/input
hashes, native session IDs and final messages, and verifies current human approval
receipts. It distinguishes real reports, diagnostics and attacks and retains the
malicious-tool decision mismatch. It never sends a network request or executes
report/source evidence. Node is used only to reconstruct the trusted frozen request.

## Prepare a fresh workspace

For example, in PowerShell, choose a new destination outside this repository:

```powershell
python -m review_tools replay --case fake-approval --workspace "$env:TEMP\oss-replay-fake-approval-new" --prepare-only
```

The command refuses existing destinations and unapproved case IDs. It copies only
archived packet, canonical request template and adapter prompt; it writes a
preparation manifest and the original command arguments adapted for the new paths.
No assistant runs, no GitHub switch changes, and no original artifact is overwritten.
Inspect replay-preparation.json: execution_authorized is false. The command and
stdin_file fields are reproduction data, not permission to execute them.

Any future model execution requires explicit approval, a fresh session, a new
study directory and current account/model availability checks. Preserve native
stdout JSONL, stderr, final text and real start/end times. Do not resume an old
thread, provide the answer key, repair responses or discard unsuccessful starts.
Reading the archived prompt as UTF-8 text restores its LF message content; native
CLI framing is still different from the hosted system/user message roles.

## Differences and controls

Recovery requested gpt-6.1-sol through Codex CLI 0.165.0, not hosted Copilot Auto's
reported gpt-4o-mini-2024-07-18. The alias is not a confirmed pinned provider snapshot.
Inputs and canonical skill/messages are preserved, while engine and native framing
differ. No observed tool actions occurred in the six completed native traces.
That observation does not prove OS-level read isolation or hosted firewall,
safeoutputs, identity, public posting, billing enforcement or phone cancellation.
The current $0 additional-usage cap is a user attestation, not a historical bill.
CLI finite transport retries are not claimed absent; six completed assessments
and two preserved startup failures are reported separately from hosted requests.

## Legacy adapter

scripts.dry_run and its historical gates use report-first-v1 exports and explicit
skill-read tool events. They cannot import the newer embedded-message recovery
into the hosted transcript paths and must not overwrite existing attempts.
Their source remains frozen for historical reproduction. Use review_tools for
this declared recovery format; no changed runtime or altered case expectation is implied.
