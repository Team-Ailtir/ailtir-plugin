# Contributing Guide

This repository is a Claude Code plugin. Contributions should preserve the command-first public interface and keep implementation skills hidden from the slash menu.

## Repository Layout

- `.claude-plugin/` - plugin and marketplace manifests.
- `commands/` - visible scoped slash command wrappers.
- `skills/` - hidden workflow implementations, local scripts, and reference material.
- `resources/` - shared assets and setup templates.
- `.mcp.json` - bundled Notion and Microsoft 365 MCP server definitions.

## Development Workflow

1. Create or update public commands in `commands/*.md`.
2. Put reusable implementation detail in `skills/<workflow>/SKILL.md`.
3. Keep non-discovered assets in `resources/`.
4. Update [README.md][readme] for user-facing workflow changes.
5. Update [INSTALL.md][install] for prerequisites, marketplace, or MCP changes.
6. Update [AGENTS.md][agents] for agent or contributor workflow changes.

## Command and Skill Rules

Public commands use short kebab-case names because the plugin namespace already supplies context. For example, use `commands/takeoff.md`, not `commands/ailtir-takeoff.md`.

Workflow skills should include:

```yaml
user-invocable: false
disable-model-invocation: true
```

Only omit `disable-model-invocation` for intentional helper knowledge, such as `ailtir-rate-library`.

Use `${CLAUDE_PLUGIN_ROOT}` for bundled scripts and references. Do not hard-code local absolute paths.

## Validation

Run these before committing plugin changes:

```bash
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
```

When adding a command wrapper, confirm its target exists:

```bash
grep -R '<skill name=' commands
```

For Python helper changes, run the edited script with representative local inputs when practical.

## Commits and Pull Requests

Use short, sentence-case commit messages consistent with history, for example `Fix Claude plugin manifest schema` or `Make plugin workflows command-first`.

Pull requests should include:

- User-visible behavior changes.
- Commands or MCP servers affected.
- Validation commands run.
- Version or marketplace changes.

[agents]: ./AGENTS.md
[install]: ./INSTALL.md
[readme]: ./README.md
