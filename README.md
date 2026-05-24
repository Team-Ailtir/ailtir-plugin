# ailtir-plugin

`ailtir-plugin` is the Claude Code plugin for Ailtir. It adds `/ailtir:*`
skills that help construction and bid teams upload tender packs, analyse
knowledge bases, ask questions of tender documents, and run specialist
workflows across business development, qualification, estimating, proposal, and
post-award activity.

The plugin is a thin assistant layer over the [Ailtir CLI][ailtir-cli]. Skills
guide Claude Code through the right prompts, checks, approval gates, and CLI
commands; the CLI handles authentication and calls to the Ailtir platform.

## Who It Is For

Use this plugin if you work with Ailtir from Claude Code and want repeatable bid
workflows instead of one-off prompts. The skills are designed for tender upload,
knowledge-base analysis, bid/no-bid decisions, compliance reviews, proposal
assembly, social value responses, quote normalization, and reporting.

## Install

Install the Ailtir CLI first:

```sh
uv tool install ailtir-cli
```

Add your `AILTIR_CLI_API_TOKEN` to `~/.claude/settings.json`, then install the
plugin marketplace entry:

```sh
claude plugin marketplace add team-ailtir/ailtir-plugin
claude plugin install ailtir@team-ailtir
```

Reload Claude Code plugins:

```text
/reload-plugins
/help
```

See [Installation][installation] and [Configuration][configuration] for the full
setup flow.

## Basic Use

Start with the core knowledge-base workflow:

```text
/ailtir:tender-upload /absolute/path/to/tender_docs.zip
/ailtir:kb-analyse <kb_id>
/ailtir:kb-list
/ailtir:kb-chat <kb_id> "What is the submission deadline?"
```

Specialist skills are available under `/ailtir:*`. Run `/help` in Claude Code
after installation to see the current skill list and invocation names.

## Repository Documentation

Contributor and maintainer guidance is split by audience:

- [AGENTS.md][agents] explains the repository structure and how to maintain
  skills.
- [CONTRIBUTING.md][contributing] explains local checks, release preparation,
  and deployment.
- [docs/][docs] contains end-user installation, configuration, and usage pages.

## License

Proprietary. Copyright Team Ailtir.

[agents]: ./AGENTS.md
[ailtir-cli]: https://github.com/Team-Ailtir/ailtir-cli
[configuration]: ./docs/configuration.md
[contributing]: ./CONTRIBUTING.md
[docs]: ./docs
[installation]: ./docs/installation.md
