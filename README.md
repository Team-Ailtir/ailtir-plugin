# ailtir-plugin

A [Claude Code][claude-code] plugin that lets you upload tender documents to the
[Ailtir][ailtir] platform directly from your AI assistant.

## What it does

The plugin adds one skill to Claude Code:

**`/ailtir:tender-upload`** — Upload a ZIP archive of tender documents to Ailtir.
Claude will help you locate the file (or accept a path directly), confirm before
uploading, and report the knowledge base ID on success.

Under the hood the skill calls the [ailtir-cli][] tool, which handles authentication
and the upload to Ailtir's cloud storage.

## Getting started

See **[docs/installation.md][]** to install the CLI and plugin.

See **[docs/configuration.md][]** to set up your Ailtir secret key.

See **[docs/usage.md][]** for invocation examples and troubleshooting.

## Quick install

```sh
# 1. Install the Ailtir CLI
uv tool install ailtir-cli

# 2. Add the marketplace and install the plugin
claude plugin marketplace add team-ailtir/ailtir-plugin
claude plugin install ailtir@team-ailtir
```

Claude Code will prompt for your `AILTIR_CLI_SECRET` on first install and store it
securely in your OS keychain.

## License

Proprietary. Copyright Team Ailtir.

[ailtir]: https://app.ailtir.ai
[ailtir-cli]: https://github.com/Team-Ailtir/ailtir-cli
[claude-code]: https://claude.ai/code
[docs/installation.md]: ./docs/installation.md
[docs/configuration.md]: ./docs/configuration.md
[docs/usage.md]: ./docs/usage.md
