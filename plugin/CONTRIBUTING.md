# Contributing Guide

This repository is a Claude plugin targeting **Claude Cowork** (claude.com/product/cowork) as its primary runtime. Contributions should preserve the unified skill-based public interface — every user-invocable workflow lives as a skill — and respect Cowork's runtime constraints (no outbound network, no `${CLAUDE_PLUGIN_ROOT}` substitution).

## Repository Layout

- `.claude-plugin/` — only `plugin.json`.
- `skills/` — every workflow as `<name>/SKILL.md`, with skill-local `scripts/`, `references/`, and `templates/`.
- `.mcp.json` — bundled Ailtir, Notion, and Microsoft 365 MCP server definitions.

There is no `commands/` folder, no `resources/` folder, and no plugin-root `scripts/` folder. Anything a skill needs (templates, helper scripts, reference material) lives inside that skill's directory.

## Cowork Constraints (Read First)

Before writing a skill, know what won't work in Cowork:

- **Outbound network is blocked** at DNS. No HTTP calls to telemetry, analytics, or external APIs from a bundled script.
- **`${CLAUDE_PLUGIN_ROOT}` does NOT resolve.** Not exported as an env var. Never use it in a SKILL.md body.
- **`${CLAUDE_SKILL_DIR}` does NOT resolve.** Same.
- **`cwd` at skill invocation is the session root, not the skill directory.** Relative paths in bash blocks like `python3 scripts/foo.py` fail.

What DOES work: Claude reads SKILL.md from an absolute path, so it can construct the absolute path to any bundled script or reference file. Describe scripts and references by skill-relative path in plain English, and Claude resolves the absolute path itself.

## Development Workflow

1. Add or update a workflow at `skills/ailtir_<short-name>/SKILL.md`. The folder name becomes the slash command `/ailtir-cowork-plugin:ailtir_<short-name>`.
2. Put bundled helpers under `skills/ailtir_<short-name>/scripts/`, reference data under `skills/ailtir_<short-name>/references/`, and templates under `skills/ailtir_<short-name>/templates/`.
3. Update [README.md][readme] for user-facing workflow changes.
4. Update [INSTALL.md][install] for prerequisites, marketplace, or MCP changes.
5. Update [AGENTS.md][agents] for agent or contributor workflow changes.

## Skill Rules

Skill folder names use the `ailtir_<short-name>` convention so Ailtir attribution appears in Cowork's skill picker.

Every SKILL.md begins with:

```yaml
---
name: <folder-name>
description: <one-line — include "Triggered by /ailtir-cowork-plugin:<folder-name>." for action skills>
---
```

For an action skill that takes free-text input, add `argument-hint: "<...>"` and reference `$ARGUMENTS` in the body.

Every skill must call `plugin_report_usage` through the bundled `ailtir` MCP
server before workflow-specific work. Use the exact folder name and current
plugin version, and keep reporting failures visible but non-blocking. Direct
HTTP telemetry from scripts remains prohibited.

### How to invoke bundled scripts

Don't write `${CLAUDE_PLUGIN_ROOT}`-anchored bash blocks. Describe the invocation in natural language so Claude resolves the absolute path itself:

> Run the bundled `scripts/create_workbook.py` helper in this skill's directory with `python3`. Pass:
> - `--output "Workbook_[Project].xlsx"`
> - `--project "[Name]"`

### How to reference bundled files

Use skill-relative paths in plain English:

> Read `references/scoring-model.md` from this skill's directory.
> Read `templates/CLAUDE.md` from this skill's directory.

For cross-skill references, name the sibling skill explicitly:

> Read `references/metadata-schema.md` from the sibling `intelligence-builder` skill's directory.

## Validation

Run these before committing plugin changes:

```bash
jq empty .claude-plugin/plugin.json
claude plugin validate .claude-plugin/plugin.json --strict
```

For Python helper changes, run the edited script with representative local inputs when practical. Helpers must be self-contained — they cannot rely on `CLAUDE_PLUGIN_ROOT` or any other plugin env var. They can rely on `__file__` for path anchoring and `AILTIR_PLUGIN_DATA` (or `~/Ailtir-Tendering` fallback) for the workspace root.

## Commits and Pull Requests

Use short, sentence-case commit messages consistent with history, for example `Fix Claude plugin manifest schema` or `Unify commands into skills`.

Bump `.claude-plugin/plugin.json` AND create a matching lightweight git tag (`vX.Y.Z`) for any marketplace-visible change. The Anthropic marketplace resolves versions from tags.

Pull requests should include:

- User-visible behavior changes.
- Skills or MCP servers affected.
- Validation commands run.
- Version and tag created.

[agents]: ./AGENTS.md
[install]: ./INSTALL.md
[readme]: ./README.md
