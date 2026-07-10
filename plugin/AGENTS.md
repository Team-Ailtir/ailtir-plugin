# Repository Guidelines

This file is the agent-facing contributor guide for the Ailtir Co-Work Plugin. `CLAUDE.md` is a symlink to this file so Claude-oriented tooling and agent-oriented tooling share one source of truth.

This plugin targets **Claude Cowork** as its primary runtime (claude.com/product/cowork). It also works in Claude Code where the runtime is more permissive, but every convention here is set for Cowork's constraints.

## Agent Responsibilities

- Keep user-facing behavior documented in [README.md][readme].
- Keep install and MCP setup instructions in [INSTALL.md][install].
- Keep human contribution workflow in [CONTRIBUTING.md][contributing].
- Do not duplicate those documents here.

## Project Structure

- `.claude-plugin/` contains the `plugin.json` manifest. Only `plugin.json` belongs here.
- `skills/` contains every user-invocable workflow, plus each skill's workflow-local `scripts/`, `references/`, and `templates/`. Each skill is a folder with a `SKILL.md`.
- `.mcp.json` declares the bundled Ailtir, Notion, and Microsoft 365 MCP servers.

There is **no** `commands/` folder, **no** `resources/` folder, and **no** plugin-root `scripts/` folder. Slash commands and skills are unified — every skill at `skills/<name>/SKILL.md` is the slash command `/ailtir-cowork-plugin:<name>`. Setup templates, bundled scripts, and brand references live inside the skill that uses them.

## Profile Architecture

From v2.13 the plugin is calibrated per **profile**. The `setup` skill writes `Context/profile.json` in the user's workspace with fields `region`, `vertical`, `currency`, `date_format`, `profile_key`, `created`, `schema_version`. `profile_key` is the concatenation `{region}-{vertical}` — currently `ireland-gc` or `uk-gc`.

Skills that need to branch on jurisdiction follow this contract:

- Read `Context/profile.json` early in the skill body. If it is missing, stop and direct the user to `/ailtir-cowork-plugin:ailtir_setup`.
- Load market-specific data from `references/{profile_key}/<file>.md` inside the same skill (or from a named sibling skill's references, as `go-no-go` does with the `bid-planner` skill's references).
- Never mix content across profiles in a single output — currency, terminology, standards, and gate lists must all come from the active profile.

When adding a new skill, if it has any jurisdiction-specific content: place references in `references/ireland-gc/` and `references/uk-gc/` subfolders from the start, and load them by `profile_key`. When adding a new profile (e.g. `uk-civil`, `us-gc`), add a sibling folder under each affected skill's `references/` — do not centralise profiles at the plugin root.

## Cowork Runtime Constraints (Important)

Empirical evidence from `/ailtir-cowork-plugin:telemetry-test` (2026-06-29) on the Cowork sandbox:

- **No outbound internet from skill scripts.** Direct HTTP calls from bundled scripts fail. Public usage and feedback reporting must go through the bundled Ailtir MCP server, whose host process can reach `api-mcp`.
- **`${CLAUDE_PLUGIN_ROOT}` does NOT resolve in Cowork.** Documented for Claude Code only. Never use it in SKILL.md bodies.
- **`${CLAUDE_SKILL_DIR}` does NOT resolve in Cowork.** Not exported as an env var. Don't rely on it.
- **`cwd` at skill invocation is the session root, NOT the skill directory.** Relative paths like `scripts/foo.py` from a bash block will fail.
- **`__file__` in Python and `$0` in bash (when called with an absolute path) ARE reliable.** Anchor any bundled-file resolution off these.

The working pattern: SKILL.md describes the work in natural language and names bundled scripts and references by skill-relative path (e.g. `scripts/create_workstation.py`, `references/scoring-model.md`, `templates/CLAUDE.md`). Claude reads SKILL.md from a known absolute path, so it can construct the absolute path to each bundled file itself.

## Editing Rules

Add new user-visible workflows as `skills/ailtir_<short-name>/SKILL.md`. The folder name becomes the slash command (`/ailtir-cowork-plugin:ailtir_<short-name>`).

**For script invocations in SKILL.md, do NOT use bash code blocks with `${CLAUDE_PLUGIN_ROOT}/...` paths.** Instead, write natural-language instructions like:

> Run the bundled `scripts/foo.py` helper in this skill's directory with `python3`. Pass `--output "..."` and `--project "..."`.

Claude will construct the absolute path itself.

For bundled references, refer to them by skill-relative path:

> Read `references/scoring-model.md` from this skill's directory.

For cross-skill references, name the sibling skill explicitly:

> Read `references/metadata-schema.md` from the sibling `intelligence-builder` skill's directory.

Every skill must begin its body with a `Usage Reporting` section that calls the
public `plugin_report_usage` tool on the bundled `ailtir` MCP server. Pass the
exact skill folder name, current plugin version, and the stable anonymous UUID
stored in `~/Ailtir-Tendering/install_id`. Create that UUID v4 once when the
file is missing. Leave a failed result visible and continue the workflow. Never
send telemetry directly from a script.

Do not commit secrets, tender documents, pricing data, Notion tokens, Microsoft 365 credentials, or generated customer workspaces.

## Verification

Run these after manifest, skill, MCP, or documentation refactors:

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

When pushing marketplace-visible changes, bump `.claude-plugin/plugin.json` AND tag the bump commit with `vX.Y.Z` matching the existing lightweight-tag pattern. The Anthropic marketplace resolves versions from tags, not from `main`.

[contributing]: ./CONTRIBUTING.md
[install]: ./INSTALL.md
[readme]: ./README.md
