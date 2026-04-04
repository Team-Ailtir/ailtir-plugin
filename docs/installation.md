# Installation

This guide walks you through installing the two components required to use the
Ailtir skills: the **Ailtir CLI** and the **Ailtir Claude Code Plugin**.

## Prerequisites

- [Claude Code][claude-code] installed and running

## Step 1 — Install the Ailtir CLI

Follow the [ailtir-cli installation guide][ailtir-cli-docs] to install the CLI.

## Step 2 — Configure your secret key

Add your `AILTIR_CLI_SECRET` to `~/.claude/settings.json`. See
[configuration.md][] for how to obtain the key and where to put it.

## Step 3 — Install the Ailtir Claude Code Plugin

Add the Ailtir marketplace to Claude Code and install the plugin:

```sh
claude plugin marketplace add team-ailtir/ailtir-plugin
claude plugin install ailtir@team-ailtir
```

## Step 4 — Verify

Reload plugins and confirm the skills are available:

```sh
/reload-plugins
/help
```

You should see `/ailtir:tender-upload`, `/ailtir:analyse`, `/ailtir:list`, and
`/ailtir:chat` listed under the `ailtir` plugin.

[claude-code]: https://claude.ai/code
[ailtir-cli-docs]: https://team-ailtir.github.io/ailtir-cli
[configuration.md]: ./configuration.md
