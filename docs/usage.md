# Usage

Use the core skills to create and query a knowledge base, then run specialist
skills against the same tender or bid context.

## Upload Tender Documents

Pass an absolute path to a ZIP archive:

```text
/ailtir:tender-upload /Users/alice/Downloads/tender_docs.zip
```

If you omit the path, Claude Code will help browse common locations such as
`~/Downloads` and `~/Documents`, then ask for confirmation before upload.

On success, the CLI returns a knowledge-base ID (`kb_id`). Keep that ID for the
next steps.

## Analyse the Knowledge Base

Trigger ingestion:

```text
/ailtir:kb-analyse <kb_id>
```

If you omit the ID, the skill lists available knowledge bases and asks you to
choose one. Ingestion can take a few minutes.

## List Knowledge Bases

Check status with:

```text
/ailtir:kb-list
```

Use this to confirm a knowledge base is `ready` before asking detailed
questions.

## Chat with a Knowledge Base

Ask a question:

```text
/ailtir:kb-chat <kb_id> "What is the submission deadline?"
```

The skill sends your question and recent conversation context to the CLI so the
answer can use the active bid context.

## Run Specialist Workflows

After the core workflow is ready, choose a specialist skill from the
[skill catalog](skills.md). Examples:

```text
/ailtir:ailtir_bd_bid-no-bid <kb_id>
/ailtir:ailtir_ta_compliance-matrix <kb_id>
/ailtir:ailtir_prop_submission-preflight <kb_id>
```

Specialist skills often ask for missing context, enforce human approval gates,
and call `ailtir` commands such as `ailtir kb chat`.

## Usage Telemetry

If `AILTIR_POSTHOG_PROJECT_TOKEN` is configured with a PostHog project token
beginning with `phc_`, the plugin records an anonymous `ailtir_skill_used` event
when an `/ailtir:` skill is invoked. The event includes the skill name and plugin
version, but not prompts, tender data, file paths, or command arguments. See
[Configuration](configuration.md) for setup.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ailtir: command not found` | CLI is not installed or not on `PATH` | Reinstall the CLI and run `ailtir version` |
| Authentication or `401` error | Missing or invalid `AILTIR_CLI_API_TOKEN` | Check [Configuration](configuration.md) |
| File path error | Relative path or missing ZIP file | Use an absolute path such as `/Users/alice/Downloads/tender_docs.zip` |
| Knowledge base not ready | Ingestion is still running | Run `/ailtir:kb-list` and wait for `ready` |
| Specialist skill lacks context | Missing `kb_id`, bid profile, or source document | Provide the requested ID or brief before continuing |
