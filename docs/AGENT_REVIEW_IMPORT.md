# Website quality-review prompt import

This is a task-scoped import, not a runtime plugin installer. The site's [AGENTS.md](../AGENTS.md), [handbook](agents/HANDBOOK.md), authorship restrictions, build instructions and validation catalogue remain authoritative. Canonical multi-agent catalogue: [FOSSLife agent review playbook](https://github.com/Kazumi7884/FOSSLife/blob/docs/unified-agent-review-20261027/docs/AGENT_REVIEW_PROMPTS.md).

## Every task, including spelling and prose

> Apply Antislop's applicable quality filter (copy, code comments, UI, responsive layout and accessibility) and Ponytail's smallest complete change discipline. Preserve authorship, existing themes and facts; don't invent portfolio achievements. Read the local handbook and the relevant numbered audit cases before editing. Check the exact edited content and relevant tests; distinguish static contracts from real browser evidence. Never auto-install, publish, run a remote model, weaken security or claim an unrun plugin executed.

## Specialist prompt selection

| Need | Borrow | Application to this repository |
| --- | --- | --- |
| Plan, debug or test | Superpowers (appropriate single skill) | Keep existing successor builds and test commands |
| Security-sensitive diff | Trail of Bits Differential Review, Sharp Edges and Insecure Defaults | Prioritise studio isolation, tokens, path handling and XSS |
| Packages and actions | Supply Chain Risk Auditor and Agentic Actions Auditor | Verify Python/Node dependencies and CI permissions |
| Static code review | Static Analysis | Reuse checked-in tools; new scanner is opt-in |
| Site layout, navigation, accessibility | Vercel Web Design Guidelines and Antislop specialist skills | Cover actual supported viewports, keyboard access and themes |
| Written pages and README | Vercel Writing Guidelines and Antislop Copywriting | Preserve the user's text, do not generate fictional facts |
| React/Next.js | Vercel React Best Practices | Not applicable to the current Python/Jinja site unless the inspected component really uses React |
| Reviewed code diff | Alibaba Open Code Review | Only with separately installed CLI or local delegation; preview scope first |

Alibaba source: https://github.com/alibaba/open-code-review. It uses Git diffs and can include untracked files in workspace review. No hidden global npm installation; no private code sent to cloud, no automatic PR merges, and no substitution of LLM findings for tests. Review the exact upstream commit in FOSSLife's `config/upstreams.json` before any tool installation.

## Import prompt for Codex, Hermes or Agent Zero

> Before responding, follow AGENTS.md and docs/agents/HANDBOOK.md. Always apply Antislop and Ponytail. Load the smallest relevant specialist review skill from the reviewed Superpowers/Trail of Bits/Vercel catalogue. For actual changed code, inspect the diff, test the successor build and affected real interactions, and run an optional, locally routed Alibaba Open Code Review only if an authorised CLI already exists. Preserve independent authorship and do not make user-facing claims without evidence. Never install dependencies, alter privileges or deploy automatically.

No model server, autonomous runner or additional agent is enabled here. Rollback consists of removing this file and its AGENTS.md pointer; website source and published content remain untouched.
