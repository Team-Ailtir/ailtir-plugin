# Repository Guidelines

This file is the agent-facing contributor guide for the Ailtir Co-Work Plugin. `CLAUDE.md` is a symlink to this file so Claude-oriented tooling and agent-oriented tooling share one source of truth.

## Agent Responsibilities

- Keep user-facing behavior documented in [README.md][readme].
- Keep install, Python, and MCP setup instructions in [INSTALL.md][install].
- Keep human contribution workflow in [CONTRIBUTING.md][contributing].
- Do not duplicate those documents here.

## Project Structure

- `.claude-plugin/` contains the `plugin.json` manifest. Only `plugin.json` belongs here.
- `skills/` contains every user-invocable workflow and reference skill, plus its workflow-local `scripts/`, `references/`, and `templates/`. Each skill is a folder with a `SKILL.md`.
- `scripts/` at plugin root contains shared infrastructure: the platform-specific Python launcher (`run_python.*`) and the fail-open telemetry wrappers (`report_skill_usage.*` and the now-unused `report_command_usage.*` retained for back-compat).
- `.mcp.json` declares bundled Notion and Microsoft 365 MCP server integrations.

There is **no** `commands/` folder and **no** `resources/` folder. Slash commands and skills have been unified — every skill at `skills/<name>/SKILL.md` is the slash command `/ailtir-cowork-plugin:<name>`. Setup templates, bundled scripts, and brand references live inside the skill that uses them.

## Editing Rules

Add new user-visible workflows as `skills/<short-name>/SKILL.md`. The folder name becomes the slash command (`/ailtir-cowork-plugin:<short-name>`). Do NOT prefix folder names with `ailtir-` — the plugin namespace already supplies that.

Use `${CLAUDE_PLUGIN_ROOT}` for bundled file references inside SKILL.md bodies — for example `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/CLAUDE.md`. The newer `${CLAUDE_SKILL_DIR}` variable resolves to the current skill's own directory and is preferred for skill-local files; both work in skill content.

Never hard-code local absolute paths such as `/home/...` or `/tmp/...` unless the output is intentionally temporary.

Invoke bundled Python helpers through the platform launchers in `scripts/`:
`run_python.sh` for macOS/Linux, `run_python.ps1` for PowerShell, and
`run_python.cmd` for cmd. Use the telemetry-specific `report_skill_usage.*`
wrappers at the top of every SKILL.md for fail-open usage reporting.

Do not commit secrets, tender documents, pricing data, Notion tokens, Microsoft 365 credentials, or generated customer workspaces.

## Verification

Run these checks after manifest, skill, MCP, or documentation refactors:

```bash
jq empty .claude-plugin/plugin.json
claude plugin validate .claude-plugin/plugin.json --strict
```

Sanity check the skill catalog matches the README's command list:

```bash
ls skills/ | sort
```

## Git Workflow

Commit messages are short and sentence case, matching recent history, for example `Add contributor guide` or `Unify commands into skills`.

When pushing marketplace-visible changes, bump `.claude-plugin/plugin.json` if installed users need `claude plugin update` to pick up the change.

[contributing]: ./CONTRIBUTING.md
[install]: ./INSTALL.md
[readme]: ./README.md
