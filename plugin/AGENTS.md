# Repository Guidelines

This file is the agent-facing contributor guide for the Ailtir Co-Work Plugin. `CLAUDE.md` is a symlink to this file so Claude-oriented tooling and agent-oriented tooling share one source of truth.

## Agent Responsibilities

- Preserve the command-first plugin interface.
- Keep user-facing behavior documented in [README.md][readme].
- Keep install, Python, and MCP setup instructions in [INSTALL.md][install].
- Keep human contribution workflow in [CONTRIBUTING.md][contributing].
- Do not duplicate those documents here.

## Project Structure

- `.claude-plugin/` contains plugin and marketplace manifests.
- `commands/` contains visible scoped slash commands, exposed as `/ailtir-cowork-plugin:<name>`.
- `skills/` contains hidden implementation workflows, plus workflow-local `scripts/` and `references/`.
- `resources/` contains shared assets and setup templates that are not auto-discovered as skills.
- `.mcp.json` declares bundled Notion and Microsoft 365 MCP server integrations.

## Editing Rules

Commands are the public API. Add new user-visible workflows as `commands/<short-name>.md`.

Skills are implementation modules. Keep workflow skills hidden with:

```yaml
user-invocable: false
disable-model-invocation: true
```

Use `${CLAUDE_PLUGIN_ROOT}` for bundled file references. Never hard-code local absolute paths such as `/home/...` or `/tmp/...` unless the output is intentionally temporary.

Invoke bundled Python helpers through the platform launchers in `scripts/`:
`run_python.sh` for macOS/Linux, `run_python.ps1` for PowerShell, and
`run_python.cmd` for cmd. Use the telemetry-specific `report_command_usage.*`
and `report_skill_usage.*` wrappers only for fail-open usage reporting.

Do not commit secrets, tender documents, pricing data, Notion tokens, Microsoft 365 credentials, or generated customer workspaces.

## Verification

Run these checks after manifest, command, skill, MCP, or documentation refactors:

```bash
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
```

For command wrapper changes, verify every `<skill name="...">` target exists under `skills/<name>/SKILL.md`.

## Git Workflow

Commit messages are short and sentence case, matching recent history, for example `Add contributor guide` or `Make plugin workflows command-first`.

When pushing marketplace-visible changes, bump `.claude-plugin/plugin.json` if installed users need `claude plugin update` to pick up the change.

[contributing]: ./CONTRIBUTING.md
[install]: ./INSTALL.md
[readme]: ./README.md
