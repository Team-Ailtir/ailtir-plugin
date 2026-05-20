# Ailtir Plugin

The Ailtir Claude Code plugin adds `/ailtir:*` skills for tender upload,
knowledge-base analysis, bid/no-bid decisions, qualification responses,
estimating workflows, proposal production, and post-award learning.

The plugin guides Claude Code through repeatable workflows. It relies on the
[Ailtir CLI][ailtir-cli] for authentication and communication with the Ailtir
platform.

## Start Here

- [Installation](installation.md): install the Ailtir CLI and Claude Code plugin.
- [Configuration](configuration.md): set `AILTIR_CLI_SECRET` and optional API
  settings.
- [Usage](usage.md): run the core upload, analyse, list, and chat workflow.
- [Skill catalog](skills.md): browse the available specialist bid workflow
  skills.

## Typical Workflow

1. Upload tender documents with `/ailtir:tender-upload`.
2. Analyse the resulting knowledge base with `/ailtir:kb-analyse`.
3. Ask questions with `/ailtir:kb-chat`.
4. Run specialist workflows such as compliance matrix, bid/no-bid, technical
   proposal, quote normalization, or submission pre-flight.

[ailtir-cli]: https://github.com/Team-Ailtir/ailtir-cli
