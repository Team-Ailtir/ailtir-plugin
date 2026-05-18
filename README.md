# ailtir-plugin

A [Claude Code][claude-code] plugin that lets you upload tender documents to the
[Ailtir][ailtir] platform directly from your AI assistant.

## What it does

The plugin adds four skills to Claude Code that cover the full Ailtir workflow:

**`/ailtir:tender-upload`** — Upload a ZIP archive of tender documents to Ailtir.
Claude will help you locate the file (or accept a path directly), confirm before
uploading, and report the knowledge base ID on success.

**`/ailtir:kb-analyse <kb_id>`** — Trigger the ingestion pipeline for a knowledge base.
If no `kb_id` is given, Claude lists your knowledge bases and asks you to pick one.

**`/ailtir:kb-list`** — List all knowledge bases in your account, showing name, `kb_id`,
and status. Nudges you toward `/ailtir:chat` when any are ready.

**`/ailtir:kb-chat <kb_id> <question>`** — Ask a natural-language question against a
knowledge base. Claude enriches the query with the last five conversation interactions
as context before calling the CLI.

Under the hood each skill calls the [ailtir-cli][] tool, which handles authentication
and communication with Ailtir's cloud platform.

## Getting started

See **[docs/installation.md][]** to install the CLI and plugin.

See **[docs/configuration.md][]** to set up your Ailtir secret key.

See **[docs/usage.md][]** for invocation examples and troubleshooting.

## Quick install

```sh
# 1. Install the Ailtir CLI
uv tool install ailtir-cli

# 2. Add your secret key to ~/.claude/settings.json
#    See docs/configuration.md for details

# 3. Add the marketplace and install the plugin
claude plugin marketplace add team-ailtir/ailtir-plugin
claude plugin install ailtir@team-ailtir
```

## License

Proprietary. Copyright Team Ailtir.

[ailtir]: https://app.ailtir.ai
[ailtir-cli]: https://github.com/Team-Ailtir/ailtir-cli
[claude-code]: https://claude.ai/code
[docs/installation.md]: ./docs/installation.md
[docs/configuration.md]: ./docs/configuration.md
[docs/usage.md]: ./docs/usage.md
