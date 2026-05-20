# Repository Guidelines

## Purpose

This file is for maintainers and coding agents changing the repository. User
installation and usage belong in [README.md][readme] and `docs/`; release steps
belong in [CONTRIBUTING.md][contributing].

## Repository Structure

- `.claude-plugin/marketplace.json` registers the Team Ailtir marketplace and
  points Claude Code at `plugins/ailtir`.
- `plugins/ailtir/.claude-plugin/plugin.json` is the plugin manifest. Keep the
  name, version, description, repository, and license accurate.
- `plugins/ailtir/.mcp.json` declares MCP servers available to the plugin.
- `plugins/ailtir/skills/*/SKILL.md` contains the skill definitions loaded by
  Claude Code.
- `docs/` contains the GitHub Pages documentation, built by the Pages workflow
  in `.github/workflows/pages.yml`.

## Skill Layout

Each skill lives in its own directory and exposes one `SKILL.md`. Directory
names are lowercase and hyphenated, with an underscore separating domain and
workflow where useful, for example `proposal_doc-assembly` or
`tender-analysis_contract-risk`.

Every `SKILL.md` starts with YAML front matter:

```yaml
---
name: ailtir_domain_workflow
description: "Short user-facing summary. Include the /ailtir: invocation."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---
```

Use `allowed-tools: Bash` for CLI-only skills. Add MCP tools only when the skill
actually needs them.

## Maintaining Skills

Keep skills operational, not promotional. A good skill defines scope, states what
it does not do, lists ordered instructions, and includes error handling for
missing configuration, missing knowledge bases, failed CLI commands, or required
human approval.

When adding or changing a skill:

1. Choose a stable invocation name and keep it consistent in the directory,
   front matter, README/docs references, and examples.
2. Prefer concrete commands such as `ailtir kb chat <kb_id> "..."`
   over vague tool descriptions.
3. Preserve approval gates for bid/no-bid, submission, credential exceptions,
   commercial thresholds, and other human decisions.
4. Do not embed customer data, secrets, portal credentials, or private tender
   content in examples.
5. Update user docs only when the change affects installation, configuration, or
   normal usage.

## Style

Use Markdown for instructions and two-space indentation for JSON. Keep headings
short, use numbered lists when sequence matters, and keep examples copy-pasteable.
Commit messages should be short imperative subjects, such as `Add qualification
skill` or `Fix plugin manifest version`.

[contributing]: ./CONTRIBUTING.md
[readme]: ./README.md
