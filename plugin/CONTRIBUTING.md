# Contributing Guide

This repository is a Claude Code plugin. Contributions should preserve the unified skill-based public interface — every user-invocable workflow lives as a skill.

## Repository Layout

- `.claude-plugin/` — only `plugin.json`.
- `skills/` — every workflow as `<name>/SKILL.md`, with skill-local `scripts/`, `references/`, and `templates/`.
- `scripts/` — shared infrastructure: platform Python launchers and telemetry wrappers.
- `.mcp.json` — bundled Notion and Microsoft 365 MCP server definitions.

There is no separate `commands/` folder and no `resources/` folder. Anything a skill needs (templates, helper scripts, reference material) lives inside that skill's directory.

## Development Workflow

1. Add or update a workflow at `skills/<short-name>/SKILL.md`. The folder name becomes the slash command `/ailtir-cowork-plugin:<short-name>`.
2. Put bundled helpers under `skills/<short-name>/scripts/` and reference data under `skills/<short-name>/references/`. Templates go under `skills/<short-name>/templates/`.
3. Update [README.md][readme] for user-facing workflow changes.
4. Update [INSTALL.md][install] for prerequisites, marketplace, or MCP changes.
5. Update [AGENTS.md][agents] for agent or contributor workflow changes.

## Skill Rules

Skill folder names use short kebab-case. The plugin namespace already supplies `ailtir-cowork-plugin:` — do NOT prefix folder names with `ailtir-`.

Every SKILL.md begins with:

```yaml
---
name: <folder-name>
description: <one-line — include "Triggered by /ailtir-cowork-plugin:<folder-name>." for action skills>
---
```

For an action skill that takes free-text input, add `argument-hint: "<...>"` and reference `$ARGUMENTS` in the body.

Every SKILL.md should fire fail-open telemetry at the top, before any workflow steps:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" <folder-name> >/dev/null 2>&1 || true
```

Plus the PowerShell and cmd variants for Windows shells.

Use `${CLAUDE_PLUGIN_ROOT}` for bundled scripts and references. The newer `${CLAUDE_SKILL_DIR}` resolves to the current skill's own folder and is preferred for skill-local files. Do not hard-code local absolute paths.

## Validation

Run these before committing plugin changes:

```bash
jq empty .claude-plugin/plugin.json
claude plugin validate .claude-plugin/plugin.json --strict
```

For Python helper changes, run the edited script with representative local inputs when practical.

## Commits and Pull Requests

Use short, sentence-case commit messages consistent with history, for example `Fix Claude plugin manifest schema` or `Unify commands into skills`.

Pull requests should include:

- User-visible behavior changes.
- Skills or MCP servers affected.
- Validation commands run.
- Version or marketplace changes.

[agents]: ./AGENTS.md
[install]: ./INSTALL.md
[readme]: ./README.md
