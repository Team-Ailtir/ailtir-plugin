# Repository Guidelines

## Project Structure & Module Organization

This repository packages the Ailtir Claude Code plugin and its documentation.
The plugin lives under `plugins/ailtir/`. Plugin metadata is in
`plugins/ailtir/.claude-plugin/plugin.json`, MCP configuration is in
`plugins/ailtir/.mcp.json`, and each skill is a directory under
`plugins/ailtir/skills/` containing a single `SKILL.md`.

Documentation for GitHub Pages is in `docs/`, with `docs/_config.yml` providing
Jekyll configuration. The root `README.md` should stay concise and point users
to the detailed docs.

## Build, Test, and Development Commands

There is no application build step or package manager lockfile in this repo.
Use these checks during development:

```sh
git status
git diff --check
find plugins/ailtir/skills -name SKILL.md | sort
```

`git diff --check` catches whitespace errors before commit. The `find` command
confirms every skill directory exposes the expected `SKILL.md` entry point.

For manual plugin validation, install the plugin through Claude Code, then run:

```sh
/reload-plugins
/help
```

Docs are built by GitHub Actions using Jekyll Pages when files under `docs/`
change on `main`.

## Coding Style & Naming Conventions

Most source files are Markdown and JSON. Use two-space indentation in JSON and
keep Markdown headings sentence-like and scannable. Skill directories use
lowercase, hyphenated names, often grouped by domain with an underscore, for
example `tender-analysis_contract-risk` or `proposal_doc-assembly`.

Each skill file must include YAML front matter with `name`, `description`,
`argument-hint` when useful, and `allowed-tools`. Keep instructions direct,
numbered where order matters, and include concrete CLI examples such as
`ailtir analyse <kb_id>`.

## Testing Guidelines

No automated test suite is currently defined. Validate changes by checking
Markdown rendering, plugin reload behavior, and the relevant skill workflow in
Claude Code. For CLI-facing skills, verify command names and arguments against
the documented Ailtir CLI behavior before updating examples.

## Commit & Pull Request Guidelines

Recent commits use short imperative subjects, for example `Add marketplace.json`
or `Fix userConfig validation`. Follow that style: start with a verb, keep the
subject specific, and avoid bundling unrelated changes.

Pull requests should describe the changed skill or doc area, include manual
validation steps, and note any user-facing command changes. Include screenshots
only for rendered documentation changes where layout or navigation is affected.

## Security & Configuration Tips

Never commit real `AILTIR_CLI_SECRET` values or customer tender data. Examples
should use placeholders such as `acli_your_key_here` and generic paths like
`/absolute/path/to/tender.zip`.
