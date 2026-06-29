---
name: feedback
description: "Captures lightweight user feedback for an Ailtir workflow: first a 1-10 rating, then the reason, then three structured AskUserQuestion follow-ups derived from the current session."
---

# Ailtir Feedback

You collect feedback without turning it into a long survey. The goal is to understand why the last Ailtir workflow was or was not useful.

## Privacy Guardrail

Before asking for free text, say:

> Avoid client names, prices, credentials, or tender-sensitive details. A short general reason is enough.

Do not ask for project names, client names, tender values, contact details, credentials, or commercially sensitive facts.

## Step 1 - Ask For Rating First

Ask the user to rate the experience from 1 to 10.

Use this wording:

> How useful was this Ailtir workflow from 1 to 10?

If the user gives anything outside 1-10, ask once for a valid number. If they decline or say `skip`, stop and do not report feedback.

## Step 2 - Ask For The Reason Second

After the rating is known, ask:

> What is the main reason for that rating? One sentence is enough.

If the user declines, continue with an empty reason. Do not pressure them for free text.

## Step 3 - Analyze The Session

Review the current conversation and identify the workflow being rated. Prefer the most recent Ailtir command or skill. If that is unclear, use `feedback` as the workflow name and `command` as the workflow kind.

Analyze the rating, the reason, and the session context. Prepare exactly three follow-up questions that help explain the rating. Each question must:

- Be specific to what happened in the session.
- Have exactly three possible answers.
- Avoid asking for sensitive tender details.
- Be answerable in one click.

Good question themes include:

- whether the output was usable as-is, needed light edits, or needed major rework
- whether the workflow understood the tender context, partly understood it, or missed key context
- whether the biggest issue was accuracy, missing detail, speed, formatting, or integration
- whether the workflow saved time, broke even, or cost time

## Step 4 - Use The Claude AskUserQuestion Tool

Use Claude Code's `AskUserQuestion` tool for the three follow-up questions when it is available. Make a single AskUserQuestion call containing exactly three questions. Each question must have exactly three options. Do not use multi-select.

Use option labels that are short and stable enough to report, for example:

- `usable_as_is`
- `needed_light_edits`
- `needed_major_rework`

Each option should include a short human-readable description.

If `AskUserQuestion` is unavailable in the current host, ask the same three questions in plain text with three numbered options each.

## Step 5 - Write Feedback to the Workspace

Append the collected rating, reason, workflow, and the three follow-up answers to the local feedback log at `<workspace-root>/Daily/feedback.md` (create the file if it doesn't exist). Workspace root resolves from `AILTIR_PLUGIN_DATA` or defaults to `~/Ailtir-Tendering`.

Use this entry format (Markdown, newest entry at the top):

```markdown
## [YYYY-MM-DD HH:MM] [workflow-name]

- Rating: [1-10]
- Reason: [reason or "(none)"]
- output_quality: [selected-option]
- context_fit: [selected-option]
- time_impact: [selected-option]
```

After writing, briefly thank the user and stop. Do not continue asking feedback questions.

## Anti-Patterns

- DO NOT ask the reason before the 1-10 rating.
- DO NOT ask more than three structured follow-up questions.
- DO NOT ask for free-text comments more than once.
- DO NOT collect sensitive tender, pricing, client, credential, or personal details.
- DO NOT fail the user workflow if feedback reporting fails.

## Quality Checks

- [ ] Rating was requested first.
- [ ] Reason was requested second.
- [ ] Exactly three follow-up questions were prepared from session context.
- [ ] Each follow-up question had exactly three possible answers.
- [ ] AskUserQuestion was used when available.
- [ ] Feedback reporting was fail-open.
