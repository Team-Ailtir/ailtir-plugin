# Changelog

This changelog was reconstructed from commits that changed the plugin manifest
version. Entries use those version bumps as release boundaries.

## 2.10.2 - 2026-06-29

Commit: `33bdec6` - `Bump version to 2.10.2`

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
