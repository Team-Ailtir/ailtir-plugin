# Configuration

The plugin uses the Ailtir CLI, so Claude Code must have access to the same
environment variables the CLI expects.

## Required Secret

Set `AILTIR_CLI_SECRET` in `~/.claude/settings.json`:

```json
{
  "env": {
    "AILTIR_CLI_SECRET": "acli_your_key_here"
  }
}
```

To get the key:

1. Sign in to [app.ailtir.ai][app].
2. Open **Account** from your user menu.
3. Reveal the CLI key in the **Secrets** section.
4. Copy the value beginning with `acli_`.

If `settings.json` already exists, add the key inside the existing `env` object
rather than replacing unrelated settings.

## Optional API URL

By default, the CLI talks to `https://app.ailtir.ai/cli-api`. For a self-hosted
or non-production environment, add `CLI_API_URL`:

```json
{
  "env": {
    "AILTIR_CLI_SECRET": "acli_your_key_here",
    "CLI_API_URL": "https://your-instance.example.com/cli-api"
  }
}
```

## Rotate a Key

Replace the `AILTIR_CLI_SECRET` value in `~/.claude/settings.json`, then reload
Claude Code plugins:

```text
/reload-plugins
```

## Security Notes

Do not paste real secret keys into prompts, commits, screenshots, or support
tickets. Use placeholders such as `acli_your_key_here` when sharing examples.

[app]: https://app.ailtir.ai
