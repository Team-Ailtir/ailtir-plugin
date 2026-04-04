# Configuration

The plugin requires one secret: your **Ailtir CLI secret key** (`AILTIR_CLI_SECRET`).

## Obtaining your CLI secret key

1. Sign in to [app.ailtir.ai][app]
2. Click your avatar in the top right → **Account**
3. Find the **Secrets** section and click **Reveal**
4. Copy the CLI Key — it starts with `acli_`

## Setting the secret

Add `AILTIR_CLI_SECRET` to the `env` section of your Claude Code user settings file
(`~/.claude/settings.json`):

```json
{
  "env": {
    "AILTIR_CLI_SECRET": "acli_your_key_here"
  }
}
```

If `settings.json` does not exist yet, create it with that content. If it already
exists, add `AILTIR_CLI_SECRET` alongside any existing keys in the `env` object.

## Updating the secret

To rotate your key, edit `~/.claude/settings.json` and replace the value.

## Advanced: custom API URL

By default the CLI talks to `https://app.ailtir.ai/cli-api`. If you are running a
self-hosted Ailtir instance, add `CLI_API_URL` to the same `env` block:

```json
{
  "env": {
    "AILTIR_CLI_SECRET": "acli_your_key_here",
    "CLI_API_URL": "https://your-instance.example.com/cli-api"
  }
}
```

[app]: https://app.ailtir.ai
