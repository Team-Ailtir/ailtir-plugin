# Changelog

This changelog was reconstructed from commits that changed the plugin manifest
version. Entries use those version bumps as release boundaries.

## 2.15.4 - 2026-07-11

- Added an occasional feedback invitation after the first completed workflow,
  then at most every 5 completed workflows or 10 days.
- Added transparent reporting and Ailtir connector onboarding to setup.

## 2.15.3 - 2026-07-10

- Pre-approved `plugin_report_usage` while every Ailtir skill is active.
- Pre-approved `plugin_feedback` only while the feedback skill is active.

## 2.15.2 - 2026-07-10

- Restored the stable anonymous installation UUID used by earlier telemetry.
- Usage and feedback now reuse `~/Ailtir-Tendering/install_id` as the PostHog distinct ID.

## 2.15.1 - 2026-07-10

- Replaced the local `uvx` Ailtir MCP definition with the hosted Streamable
  HTTP endpoint so Cowork can install the connector directly.
- Updated all usage and feedback events to report plugin version 2.15.1.

## 2.15.0 - 2026-07-10

- Added `ailtir-mcp` 2.1.0 as a pinned bundled MCP server without an MCP token.
- Added minimal anonymous `plugin_report_usage` calls to all 34 skills.
- Replaced local feedback logging with the public `plugin_feedback` tool.
- Kept usage and feedback failures visible but non-blocking.

## 2.14.1 - 2026-07-10

Commit: `dc878f2` - `Bump version to 2.14.1`

- Bumped plugin version from 2.14.0 to 2.14.1.

## 2.14.0 - 2026-07-02

Rebranded skill invocation to surface Ailtir attribution in Cowork's skill picker. **Breaking change to slash-command paths.**

- Renamed every skill directory from `<name>` to `ailtir_<name>` (e.g. `bid-assembly` → `ailtir_bid-assembly`). Cowork's skill picker labels skills by directory name — not by SKILL.md `name:` frontmatter — so folder renames are required to affect the picker display. Underscore separator chosen because `:` is illegal in Windows/git paths and `-` would collide with the plugin namespace prefix.
- Every slash command changed accordingly: `/ailtir-cowork-plugin:bid-assembly` → `/ailtir-cowork-plugin:ailtir_bid-assembly`. Any external references (bookmarks, docs, workflows) must be updated.
- Updated 40 in-repo slash-command references across SKILL.md files, `README.md`, `INSTALL.md`, `AGENTS.md`, `commands/setup.md`, and the Ireland/UK CLAUDE.md templates.
- Updated `name:` frontmatter in all 33 SKILL.md files to match the new directory names.

## 2.13.1 - 2026-07-02

- Rebranded skill display names in SKILL.md `name:` frontmatter to `ailtir:<skill>`. Superseded by 2.14.0 — Cowork ignores the `name:` field and reads directory names instead.

## 2.12.1 - 2026-06-29

- Removed the diagnostic `telemetry-test` skill. Its job (proving Cowork's sandbox blocks outbound network and doesn't substitute `${CLAUDE_PLUGIN_ROOT}`) is done; future revisits can resurrect it from git history if needed. The plugin now ships with zero telemetry surface and 32 user-invocable skills.

## 2.12.0 - 2026-06-29

Cowork-first refactor. The Cowork sandbox blocks outbound network at DNS, does not substitute `${CLAUDE_PLUGIN_ROOT}` or `${CLAUDE_SKILL_DIR}`, and `cwd` at skill invocation is the session root rather than the skill directory — so every `${CLAUDE_PLUGIN_ROOT}`-anchored bash block in the plugin had been silently failing in production. This release fixes that.

- Removed `${CLAUDE_PLUGIN_ROOT}` from every SKILL.md. Script invocations and bundled-file references are now described in natural language; Claude resolves the absolute path from the SKILL.md's known location.
- Deleted the plugin-root `scripts/` folder. The telemetry wrappers (`report_skill_usage.*`, `report_command_usage.*`), the PostHog reporter (`report_usage.py`, `report_feedback.py`), and the Python launchers (`run_python.*`) are all gone. The PostHog pipeline cannot function in Cowork (egress blocked) and was unused after the SKILL.md rewrites.
- Stripped the `## Usage Reporting` bash block from all 33 SKILL.md files.
- `feedback` skill now writes feedback to a local `Daily/feedback.md` in the workspace instead of POSTing to PostHog.
- `setup`, `prime`, `bid-planner`, `bid-leveling`, `package-breakdown`, `takeoff`, `project-indexer` rewrote their Python-helper invocations as natural-language instructions.
- Updated AGENTS.md and CONTRIBUTING.md to document the Cowork runtime constraints and the new script-invocation pattern.

## 2.11.1 - 2026-06-29

- Added probe #2 to the `telemetry-test` skill (`scripts/test_egress_and_paths.py`). Tests which hosts the Cowork sandbox proxy allows outbound to, and dumps how `${CLAUDE_SKILL_DIR}` / `${CLAUDE_PLUGIN_ROOT}` resolve in the runtime environment.

## 2.11.0 - 2026-06-29

- Unified commands and skills into a single `skills/` tree. The `commands/` and `resources/` folders are removed.
- Dropped the redundant `ailtir-` prefix from all skill folders; the plugin namespace already supplies it. Slash commands stay `/ailtir-cowork-plugin:<name>`.
- Folded `commands/setup.md`, `commands/prime.md`, and `commands/enable-monitor.md` into new skills under `skills/setup/`, `skills/prime/`, and `skills/enable-monitor/`.
- Moved setup templates and the workstation creator into `skills/setup/`, the Notion cache sync script into `skills/prime/scripts/`, and the brand reference into `skills/dashboard/references/`.
- Added a `telemetry-test` skill that probes whether relative-path bundled scripts execute in Cowork and whether PostHog egress is reachable. Use it once per deployment to determine whether the per-skill telemetry pattern can function.

## 2.10.3 - 2026-06-29

Commit: `09a6d3d` - `Fix telemetry on Python 3.14 and bump to 2.10.3 (#3)`

- Fixed telemetry silently dropping on Python 3.14 hosts. The interpreter's new strict X.509 verification rejects PostHog's TLS chain because an intermediate CA cert is missing the critical flag on its Basic Constraints extension; the telemetry helper now relaxes that one flag and matches prior behaviour.

## 2.10.2 - 2026-06-29

Commit: `a8a53dd` - `Fix Windows Python resolution and bump to 2.10.2 (#2)`

- Fixed Windows Python resolution: the launcher now skips the Microsoft Store python.exe App Execution Alias stubs and prefers the py launcher on Windows.
- Fixed sync_notion_cache.py writing the mock cache with the platform default codec; the script now writes utf-8 so non-Latin-1 glyphs survive on Windows hosts.

## 2.10.1 - 2026-06-18

Commit: `baac213` - `Bump version to 2.10.1`

- Fixed telemetry reporting when Claude invokes plugin helper scripts by
  absolute path without exporting `CLAUDE_PLUGIN_ROOT` to the Python process.

## 2.10.0 - 2026-06-18

Commit: `eb86ab9` - `Bump version to 2.10.0`

- Made the Ailtir workspace root configurable with `AILTIR_PLUGIN_DATA`.
- Moved anonymous install ID storage under `AILTIR_PLUGIN_DATA`.
- Removed user-facing documentation for Claude runtime-only plugin variables.
- Made telemetry fail fast when Claude does not provide the plugin root runtime
  environment.
- Bundled telemetry configuration in the plugin so users no longer configure
  PostHog project token, host, timeout, or debug environment variables.

## 2.9.0 - 2026-06-17

Commit: `b6fd577` - `Bump version to 2.9.0`

- Added the `/ailtir-cowork-plugin:feedback` command.
- Added a hidden `ailtir-feedback` workflow that collects a 1-10 usefulness
  rating, the reason for the rating, and three structured follow-up answers.
- Added fail-open feedback reporting through `ailtir_feedback_submitted`.
- Added root `.gitignore` coverage for Python build and cache artifacts.

## 2.8.1 - 2026-06-16

Commit: `34fd10c` - `Add command usage telemetry`

- Added usage reporting blocks to all user-facing commands.
- Added cross-platform command telemetry wrappers.
- Renamed the shared telemetry implementation to `report_usage.py` so it covers
  both command and skill usage.
- Standardized bundled helper execution through the Python launcher scripts.

## 2.8.0 - 2026-06-16

Commit: `822a217` - `Add cross-platform skill telemetry`

- Added fail-open skill usage telemetry to hidden workflow skills.
- Added cross-platform skill telemetry wrappers.
- Moved the installable package under `plugin/` and made the repository
  marketplace wrapper point at that package.
- Removed the duplicate root plugin manifest after the package move.

## 2.7.1 - 2026-06-15

Commit: `843f71f` - `Bumping the version to 2.7.1`

- Refactored repository documentation.
- Added the contributor guide.
- Documented `unzip` as an installation prerequisite.

## 2.7.0 - 2026-06-11

Commit: `5f9d926` - `Make plugin workflows command-first`

- Made scoped slash commands the public workflow interface.
- Added command wrappers for the broader tender-management workflow set.
- Kept detailed implementation behavior in hidden skills.
- Moved setup resources into the shared `resources/setup` layout.

## 2.6.1 - 2026-06-10

Commit: `3620e9a` - `Bump version for setup command update`

- Updated the setup command flow.
- Scoped the setup command to the Co-Work plugin command namespace.
- Restored the V2 marketplace entry after removing V1 documentation and
  publishing workflow leftovers.
- Fixed the Claude plugin manifest schema.

## 2.6.0 - 2026-06-10

Commit: `ec28343` - `V2: Initial commit`

- Introduced the Ailtir Co-Work plugin line.
- Added the full Irish construction tender-management workflow set.
- Added commands, hidden skills, setup resources, MCP configuration, workbook
  helpers, takeoff scripts, and dashboard support.
- Established the CWMF-focused workflow from opportunity monitoring through
  estimating, submission, post-award records, and bid intelligence.

## 2.0.0 - 2026-05-24

Commit: `4f1ddc9` - `Rename core KB skills`

- Renamed the core knowledge-base skills to the `ailtir_kb_*` naming pattern.
- Updated docs and skill references to match the renamed core skills.

## 1.2.0 - 2026-05-24

Commit: `d338e44` - `Bump version to 1.2.0`

- Added the first business-development skill and validated nested plugin paths.
- Added 28 agent skills covering the broader Ailtir tendering workflow.
- Added repository and plugin documentation updates.
- Added early skill usage telemetry and telemetry setup documentation.

## 1.1.0 - 2026-04-04

Commit: `1005108` - `Bump version to 1.1.0`

- Moved the plugin under `plugins/ailtir/` and added marketplace metadata.
- Added analyze, list, and chat skills alongside tender upload.
- Updated docs for the expanded CLI workflow.
- Reworked `AILTIR_CLI_SECRET` configuration handling.

## 1.0.0 - 2026-04-04

Commit: `6e3941f` - `Add ailtir Claude Code plugin with tender-upload skill`

- Added the original `ailtir` Claude Code plugin.
- Added the tender-upload skill backed by the Ailtir CLI.
- Added initial MCP configuration and docs for installation, configuration, and
  usage.

## History Notes

- The original `ailtir` V1 plugin line was removed in commit `3f0358b` on
  2026-06-10.
- The current `ailtir-cowork-plugin` line began with version `2.6.0`.
- Commit `c1ecc0a` moved the Co-Work plugin into the current nested `plugin/`
  package layout without changing the version number.
