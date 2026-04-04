# Configuration

The plugin requires one secret: your **Ailtir CLI secret key** (`AILTIR_CLI_SECRET`).

## Obtaining your CLI secret key

1. Sign in to [app.ailtir.ai][app]
2. Click your avatar in the top right → **Account**
3. Find the **Secrets** section and click **Reveal**
4. Copy the CLI Key — it starts with `acli_`

## How the secret is stored

When you install the plugin, Claude Code will prompt:

> Enter value for AILTIR_CLI_SECRET (your Ailtir CLI secret key — starts with acli_):

Claude Code stores the value securely in your OS keychain and injects it as the
`AILTIR_CLI_SECRET` environment variable whenever a skill runs. You will not need to
set it manually.

## Updating the secret

If you need to update the stored value (e.g., after rotating your key):

```sh
claude plugin config set ailtir AILTIR_CLI_SECRET
```

Claude Code will prompt for the new value and update the keychain entry.

## Advanced: custom API URL

By default the CLI talks to `https://app.ailtir.ai/cli-api`. If you are running a
self-hosted Ailtir instance, set `CLI_API_URL` in your environment before invoking
the skill:

```sh
export CLI_API_URL=https://your-instance.example.com/cli-api
```

[app]: https://app.ailtir.ai
