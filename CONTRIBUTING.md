# Contributing

This repository ships a Claude Code plugin. It has no application build step;
validation is mostly manifest checks, Markdown review, and manual plugin testing
inside Claude Code.

## Local Checks

Before opening a pull request, run:

```sh
git status
git diff --check
find plugins/ailtir/skills -name SKILL.md | sort
```

Review changed Markdown in your editor or a Markdown preview. For JSON changes,
validate syntax with:

```sh
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool plugins/ailtir/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/ailtir/.mcp.json >/dev/null
```

## Manual Plugin Test

Install the local plugin through Claude Code using the marketplace entry, then
reload plugins:

```text
/reload-plugins
/help
```

Confirm the changed skill appears under `/ailtir:*`. Run the skill far enough to
verify argument parsing, required confirmations, CLI command spelling, and error
handling. For CLI workflows, test with a non-production knowledge base or mocked
inputs when possible.

## Preparing a Version

1. Update `plugins/ailtir/.claude-plugin/plugin.json` with the new semantic
   version.
2. If the marketplace description or install-time configuration changed, update
   `.claude-plugin/marketplace.json`.
3. Update `README.md` or `docs/` only for user-visible behavior changes.
4. Re-run the local checks and manual plugin test.
5. Commit with an imperative message, for example `Bump version to 1.2.0`.

## Pull Requests

Pull requests should include:

- What changed and why.
- Which skill, manifest, or doc area was touched.
- Manual validation steps and results.
- Any new CLI commands, required environment variables, or approval gates.

Keep unrelated skill rewrites out of the same PR. Include screenshots only for
rendered documentation changes where layout or navigation changed.

## Deployment

Plugin deployment is repository based. After review, merge the release commit to
`main` and push the updated manifest and skills. Consumers receive the new
plugin version through the Claude Code marketplace source.

Documentation deploys separately: pushes to `main` that change `docs/**` or the
Pages workflow trigger `.github/workflows/pages.yml`, which builds `docs/` with
Jekyll Pages and publishes to GitHub Pages.

## Secrets

Never commit real `AILTIR_CLI_API_TOKEN` values, customer tender packs, generated
bid workspaces, or private portal material. Use placeholders such as
`acli_your_key_here` and `/absolute/path/to/tender.zip`.
