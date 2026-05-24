# Installation

Install two components before using the Ailtir skills: the Ailtir CLI and the
Ailtir Claude Code plugin.

## Prerequisites

- [Claude Code][claude-code] installed and running.
- Access to an Ailtir account with a CLI secret key.
- `uv` available if you install the CLI with `uv tool install`.

## 1. Install the Ailtir CLI

Install the CLI:

```sh
uv tool install ailtir-cli
```

Confirm it is available on your shell path:

```sh
ailtir version
```

If your environment uses another installation method, follow the
[Ailtir CLI documentation][ailtir-cli-docs].

## 2. Configure Your Secret

Add `AILTIR_CLI_SECRET` to `~/.claude/settings.json`. See
[Configuration](configuration.md) for the expected file format and optional
`CLI_API_URL` setting.

## 3. Install the Plugin

Add the Ailtir marketplace and install the plugin:

```sh
claude plugin marketplace add team-ailtir/ailtir-plugin
claude plugin install ailtir@team-ailtir
```

## 4. Install in Claude CoWork

Claude CoWork installs plugins from the Claude Desktop app. Use this path when
you want the Ailtir skills available in CoWork instead of, or in addition to,
Claude Code.

1. Open the Claude Desktop app and switch to **CoWork**.
2. Open **Customize** in the left sidebar, then select **Plugins**.
3. Select **Add marketplace**.
4. Enter the Ailtir plugin repository:

   ```text
   team-ailtir/ailtir-plugin
   ```

   If CoWork asks for a full URL, use:

   ```text
   https://github.com/team-ailtir/ailtir-plugin
   ```

5. Select the Ailtir plugin from the marketplace and click **Install**.
6. Open the installed plugin and confirm that the Ailtir skills are listed.

If your organization distributes plugins centrally, the Ailtir plugin may appear
under your organization-managed plugins instead of requiring a manual marketplace
entry. If you received a packaged plugin file, use the upload option on the
Plugins page and select that package.

## 5. Verify in Claude Code

Reload plugins and inspect the available commands:

```text
/reload-plugins
/help
```

You should see core commands such as `/ailtir:tender-upload`,
`/ailtir:kb-analyse`, `/ailtir:kb-list`, and `/ailtir:kb-chat`, plus the
specialist skills listed in the
[skill catalog](skills.md).

[ailtir-cli-docs]: https://team-ailtir.github.io/ailtir-cli
[claude-code]: https://claude.ai/code
