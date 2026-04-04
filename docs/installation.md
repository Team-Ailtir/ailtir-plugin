# Installation

This guide walks you through installing the two components required to use the
`/ailtir:tender-upload` skill: the **Ailtir CLI** and the **Ailtir Claude Code Plugin**.

## Prerequisites

- [Claude Code][claude-code] installed and running
- [uv][] installed (recommended) or `pip`

## Step 1 — Install the Ailtir CLI

The Ailtir CLI is the underlying tool that handles the upload. Install it with `uv`:

```sh
uv tool install ailtir-cli
```

Or with `pip`:

```sh
pip install ailtir-cli
```

Verify it installed correctly:

```sh
ailtir version
```

You should see the current version number printed.

## Step 2 — Install the Ailtir Claude Code Plugin

Add the Ailtir marketplace to Claude Code and install the plugin:

```sh
claude plugin marketplace add team-ailtir/ailtir-plugin
claude plugin install ailtir@team-ailtir
```

During installation, Claude Code will prompt you for your **Ailtir CLI secret key**.
See [configuration.md][] for how to obtain it.

## Step 3 — Verify

Reload plugins and confirm the skill is available:

```sh
/reload-plugins
/help
```

You should see `/ailtir:tender-upload` listed under the `ailtir` plugin.

[claude-code]: https://claude.ai/code
[uv]: https://docs.astral.sh/uv/getting-started/installation/
[configuration.md]: ./configuration.md
