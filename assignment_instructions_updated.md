Configure an existing AI agent to support a real open-source workflow, test the configuration on historical cases, and justify your design decisions. Both the configuration and its justification will be assessed.

Choosing a workflow
Choose a workflow in an open-source project, such as issue triage, first-pass PR review, CI-failure analysis, duplicate detection, or changelog drafting. Explain why an AI agent is appropriate for this workflow rather than conventional automation. Use repository data to establish the need for automation (e.g., time to first issue response or number of PRs awaiting review). State what you measured, over which period, and the limitations of the metric.

You may also base the assignment on a project of your own. If it is too small to provide meaningful repository data, say so and argue the need for automation from the workflow itself.

Students may choose the same project and workflow, but must develop and evaluate their configurations independently.

What to do
1. Configure the agent
Implement the following:

Workflow: A GitHub Agentic Workflow (or platform equivalent) with a trigger, explicit permissions, allowed tools, safe outputs with limits, and a timeout. Restrict network access where supported. The agent must not be able to close or delete issues, merge PRs, or force-push.
AGENTS.md: Repository instructions covering build and test commands, project structure, conventions, and forbidden changes.
Claude Skill: A SKILL.md defining the procedure the agent follows, with supporting scripts where useful. Automate checks that do not require model judgement, such as label validation or duplicate searches. Verify that the agent running your workflow loads and uses the skill.
CONTRIBUTING.md: An AI-contribution policy if the workflow produces material that humans later submit, or if its rules apply to all contributors.
Put each rule where it can be enforced. Repository facts belong in `AGENTS.md`, procedures in the skill, and hard restrictions in workflow permissions and safe outputs. An instruction telling the model not to perform an action is not a substitute for preventing that action.

2. Test the configuration
Run the agent in a sandbox repository you control, using a copy or representative subset of the original project. Do not deploy it to someone else's project without permission.

Collect at least 10 real historical inputs (issues, PRs, CI failures, etc.), including cases requiring no action. Preserve the context needed to evaluate each case (e.g., relevant repository files, issue history, or CI logs), avoiding information that became available only after the original event. Record the expected outcome for each case before running the agent. Additionally, construct at least one adversarial input to test the agent's safeguards.

If you are using a project of your own that lacks historical inputs, you may create the inputs yourself, for example by opening the issues or PRs that the workflow would handle. Make them realistic and varied, include cases requiring no action, and record the expected outcome for each case before running the agent, as above.

Run the agent and compare its actual output with the expected outcome for every case. Report all failures and explain them. A successful workflow execution does not establish that the agent made the correct decisions.

If end-to-end execution is not possible, explain why and conduct a dry run using a coding assistant with the same configuration and inputs. Keep the transcripts and identify which controls you could not test.

You do not need to use Claude as the workflow engine, and you are not expected to pay for API access. For example, GitHub Copilot for students (https://github.com/education/students) is free for students and includes AI usage credits. If you cannot run the workflow end to end, use the dry-run alternative above and document what you tested and which controls you could not verify.

3. Govern the agent
For each control below, implement it or explain why it is unnecessary or unsupported. Choose controls based on the actions your agent can perform, rather than implementing mechanisms that serve no purpose.

Identity: Agent actions are attributed to a bot or application, not a personal account.
Least privilege: Read-only permissions by default.
Safe outputs: Explicitly allowed actions with enforced limits.
Human approval: Required reviews, draft PRs, or CODEOWNERS where appropriate.
Budgets: Limits on runs, outputs, runtime, and model usage.
Audit trail: Records of triggers, model versions, tool calls, outputs, and costs where available.
Kill switch: A mechanism for maintainers to stop the agent, including handling running executions.
Drift detection: When golden tasks are rerun, which outputs humans review, and who reviews them.
Accountability: Who can change or disable the configuration, and who is responsible for the agent's actions.
Distinguish implemented and tested controls from those that are only proposed. Identify the untrusted inputs the agent reads and the actions it can perform.

Answer five questions, referring to your configuration:

An issue instructs the agent to close all stale issues and claims maintainer approval. What happens? Test this case.
The provider updates the model and a golden task starts failing. How and when would you detect this?
The project receives 300 issues in one week. What happens under your rate limits?
A tool or MCP server returns malicious instructions. What can the agent still do?
A maintainer needs to stop the agent using only a phone. What steps are required?
4. Justify the design
In DESIGN.md, explain why you chose this workflow, why the controls fit its risks, one alternative you rejected, what you deliberately prevented the agent from doing, what your tests revealed, and what remains unresolved. For each governance control, briefly explain how it is implemented or why it is absent, referring to the relevant configuration files.

Deliverables
Submit a Git repository containing:

Configuration: Workflow files in .github/workflows/ (including the compiled .lock.yml for GitHub Agentic Workflows), AGENTS.md, .claude/skills/<name>/SKILL.md, supporting scripts, and CONTRIBUTING.md where applicable.
evals/golden/: Historical inputs, expected outcomes, actual outputs, and test logs, with instructions for reproducing the evaluation.
DESIGN.md: Your design justification, governance summary, an agent bill of materials, and answers to the five questions. The bill of materials must identify the model (including whether its version is pinned), instructions, tools and MCP servers, permissions, data sources, logs, evaluations, and responsible humans. End with an AI-use statement identifying which parts you wrote, which were AI-generated, and how you verified them.
DESIGN.md must not exceed 150 lines, including headings and blank lines. Use normal Markdown formatting rather than combining paragraphs into unusually long lines. There is no length restriction on configuration files, evaluation data, or logs.

Submission
Submit one GitHub link through eLearn, pointing to the specific commit you want marked. If the repository is private, add GitHub user ctreude as a collaborator before submitting.

All required files must be present at that commit. Later commits will not be marked. No PDF is required.

You may use AI tools throughout the assignment, but you must be able to explain every part of your submission.