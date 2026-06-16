# Installation Guide

This guide installs the Ailtir Co-Work Plugin and prepares its MCP integrations.

## Prerequisites

- Claude Code with plugin support.
- Python 3 available as `python3`, `python`, or the Windows `py` launcher. Several workflows run bundled Python helper scripts through `scripts/run_python.*`.
- Node.js with `npx`. The bundled Notion and Microsoft 365 MCP servers are launched with `npx`.
- `unzip` available on `PATH` for tender pack extraction and archive handling.
- Access to the `Team-Ailtir/ailtir-plugin` GitHub repository or marketplace.

Verify local tools:

```bash
python3 --version
node --version
npx --version
unzip -v
claude --version
```

## Install the Marketplace and Plugin

Add or refresh the Team Ailtir marketplace:

```bash
claude plugin marketplace add team-ailtir/ailtir-plugin
claude plugin marketplace update team-ailtir
```

Install the plugin:

```bash
claude plugin install ailtir-cowork-plugin@team-ailtir -s user
```

After updates, refresh the installed plugin:

```bash
claude plugin update ailtir-cowork-plugin@team-ailtir -s user
```

Restart Claude Code or run `/reload-plugins` if available in your session.

## Configure MCP Servers

The plugin includes `.mcp.json` with two MCP servers:

| Server | Command | Required Credentials |
|---|---|---|
| `notion` | `npx -y @modelcontextprotocol/server-notion` | `NOTION_API_KEY` |
| `m365` | `npx -y @modelcontextprotocol/server-m365` | `M365_TENANT_ID`, `M365_CLIENT_ID`, `M365_CLIENT_SECRET` |

Configure these credentials in Claude Code using your normal secure settings or connector configuration flow. Do not commit secrets to this repository.

Use Notion when you want Ailtir to create or update CRM, Bid Pipeline, Subcontractor Directory, and RFI Log databases. Use Microsoft 365 when project documents live in SharePoint or OneDrive.

## Initialize an Ailtir Workspace

Run the setup command:

```text
/ailtir-cowork-plugin:setup
```

If using Notion, create the workspace databases:

```text
/ailtir-cowork-plugin:notion-setup
```

To enable automated opportunity monitoring, connect email and Notion first, then run:

```text
/ailtir-cowork-plugin:enable-monitor
```

If a connector is unavailable, workflows should fall back to local Markdown or CSV outputs and tell the user what was skipped.

## Validate an Installation

From this repository, validate manifests before publishing changes:

```bash
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
```

After installation, inspect the plugin:

```bash
claude plugin list
claude plugin details ailtir-cowork-plugin@team-ailtir
```
