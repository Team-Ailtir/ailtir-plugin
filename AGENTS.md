# Repository Guidelines

## Project Structure & Module Organization

This repository is a Claude Code plugin for Ailtir tender workflows.

- `.claude-plugin/` contains plugin and marketplace manifests.
- `commands/` contains visible scoped slash commands, exposed as `/ailtir-cowork-plugin:<name>`.
- `skills/` contains hidden implementation workflows in `*/SKILL.md`, plus workflow-local `scripts/` and `references/`.
- `resources/` contains shared assets and setup templates that are not auto-discovered as skills.
- `.mcp.json` declares bundled MCP server integrations.

Keep README focused on user installation and usage. Keep this file focused on contributor workflow.

## Build, Test, and Development Commands

- `claude plugin validate .claude-plugin/plugin.json --strict` validates plugin metadata and discovered components.
- `claude plugin validate .claude-plugin/marketplace.json --strict` validates marketplace metadata.
- `jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json` checks JSON syntax.
- `claude plugin marketplace update team-ailtir` refreshes the installed marketplace cache after pushing.
- `claude plugin update ailtir-cowork-plugin@team-ailtir -s user` updates the user install after a version bump.

There is no project-wide build step. Python helper scripts are invoked by commands and skills as needed.

## Coding Style & Naming Conventions

Use kebab-case for command files and skill directories. Public command names should be short and scoped by the plugin, for example `commands/takeoff.md` becomes `/ailtir-cowork-plugin:takeoff`.

Workflow skills should remain hidden with `user-invocable: false`. Use `disable-model-invocation: true` unless the skill is intentionally available as internal helper knowledge. Prefer `${CLAUDE_PLUGIN_ROOT}` in command and skill instructions when referencing bundled files.

Python scripts should be small, deterministic helpers with clear CLI arguments. Do not hard-code local absolute paths.

## Testing Guidelines

Run both `claude plugin validate` commands before committing manifest, command, skill, or MCP changes. When adding a command wrapper, verify its `<skill name="...">` target exists in `skills/<name>/SKILL.md`.

For Python helper changes, run the script directly with representative local inputs where practical.

## Commit & Pull Request Guidelines

Commit messages are short, sentence case, and imperative or descriptive, for example `Fix Claude plugin manifest schema` or `Make plugin workflows command-first`.

Pull requests should describe the user-visible plugin behavior change, list validation commands run, and note any command name or marketplace/version changes. Include screenshots only for UI-facing Claude plugin discovery changes.

## Security & Configuration Tips

Do not commit API tokens, Notion database secrets, tender pricing, or customer documents. Keep connector setup documented through `.mcp.json`, `CONNECTORS.md`, and install-time instructions rather than checked-in credentials.
