---
name: ailtir_conductor
description: Proactive lifecycle router. Scans every active bid, tells the user what phase each is in, and recommends the next skill to run. Triggered by /ailtir_conductor, or auto-invoked at the end of ailtir_prime when at least one bid exists.
---

# Ailtir Conductor — Lifecycle Router

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_conductor`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are the Ailtir plugin's proactive next-step advisor. Customers do not need to memorise the 30+ skill catalogue — this skill tells them where every bid stands and what to run next. The mode is **recommend + confirm**: name the next skill, explain in one sentence, ask the user to run it (or defer/skip/explain).

## Step 0 — Read the Profile

Read `Context/profile.json` from the workspace root. If it is missing, stop and tell the user to run `/ailtir_setup`. Do not continue without a profile.

## Step 1 — Scan the Bids

Run the bundled `scripts/scan_bids.py` helper in this skill's directory with `python3`. Pass `--bids-dir Bids/` (or omit for the default). The script returns a JSON array on stdout, one record per bid folder found under `Bids/`.

Each record has:

- `bid_id`
- `path`
- `has_frontmatter` — true if the README has a machine-readable header
- `frontmatter` — parsed dict when present (see State Contract below)
- `inferred` — dict of best-guess phase, completed[], next_action[] derived from folder contents (populated regardless of frontmatter presence)
- `warnings[]` — any parse issues

If the array is empty, tell the user "No bids found under `Bids/`. Would you like to start one with `/ailtir_bid-planner`?" and stop.

## Step 2 — Backfill Missing Frontmatter

For every bid where `has_frontmatter` is false, run the bundled `scripts/init_bid_frontmatter.py` helper with `--bid-path <path>`. The script writes a fresh frontmatter block to the top of that bid's `README.md`, using values from the `inferred` dict. Preserve any existing prose in the README (the script inserts before the `# {bid_id}` heading).

After backfilling, re-run `scripts/scan_bids.py` so every bid now has parsed frontmatter.

## Step 3 — Rank the Bids

Sort the bids by:

1. **Blockers first** — any bid with a non-empty `blockers` list (e.g. outstanding RFI, missing document) surfaces to the top.
2. **Deadline urgency** — bids with `key_dates.submission` within 14 days rank next, sorted by proximity.
3. **Staleness** — bids whose most recent `completed[]` entry is older than 5 working days.
4. **Everything else** — ordered by phase (earlier phases surface first) so nothing gets forgotten.

Present the top 3 by default. Mention the total count and offer "type `all` to see every bid".

## Step 4 — Recommend Next Actions

For each surfaced bid, print exactly this four-line block:

```text
Bid:  {project_name} — {client}
Phase: {phase} — {one-line context}
Next:  {next_skill} — {one-line rationale}
Alt:   {alt_skill_1}, {alt_skill_2}  (or "none" if no sideways moves)
```

Compute `next_skill` from `references/phase-map.md` in this skill's directory. The phase map lists, for each `phase`, the expected sequence of skills — pick the earliest expected skill not present in `completed[]`. If `blockers[]` is non-empty, override `next_skill` with the appropriate resolution skill (e.g. `ailtir_rfi-generator` for a `type: rfi` blocker).

## Step 5 — Prompt the User

For the top bid, render an **interactive HTML artifact** with clickable option
cards — the same mechanism `ailtir_bid-planner` uses for its "Tender details"
form, which Cowork renders as a real interactive surface. Emit a single self-
contained HTML block (inline CSS, no external assets) containing:

- A short heading: `Run {next_skill} for {project_name}?`
- One clickable card per action, each with a title and one-line description:
  - **Run it** — hand off to the recommended skill
  - **Explain** — show what the skill does first
  - **Defer this bid** — skip to the next bid
  - **Skip this step** — mark it skipped and move on
  - **Pick another bid** — choose a different surfaced bid
  - **Quit** — stop
- A **Submit** button that writes the chosen action back into the chat as a
  plain message (e.g. `conductor: run it`), exactly as the bid-planner form's
  submit button writes its answers back. The conductor reads that message on
  the next turn and runs the matching action below.

Keep the cards visually consistent with the bid-planner style: bordered cards,
icon or bold title, muted description line, dark-theme friendly.

**Fallback:** if the HTML artifact does not render (older host, or the user
asks for text), print this plain menu and read the typed reply instead:

> Run `{next_skill}` now? [Y = run it / d = defer this bid / s = skip this step / e = explain what it does / o = pick another bid / q = quit]

Handle the response (card submission or typed letter map to the same actions):

- **Y** — Tell the user: *"Please run `/{next_skill}` on `{bid_path}` now. When it finishes, run `/ailtir_conductor` again to see what's next."* Do **not** try to invoke the skill directly — Cowork does not chain slash commands from inside a skill. The user does the invocation; the conductor re-enters on the next turn.
- **d** — Run `scripts/update_frontmatter.py --bid-path <path> --set next_action.reason "Deferred by user on {today}"`. Move to the next bid.
- **s** — Ask why briefly, then run `scripts/update_frontmatter.py --bid-path <path> --skip {next_skill} --reason "<user's reason>"`. The skill gets appended to `completed[]` with `result: skipped`. Move on.
- **e** — Read the relevant paragraph from `references/skill-catalogue.md` in this skill's directory, print it, then re-present the Step 5 choice (the HTML card artifact, or the text menu if that is the active mode).
- **o** — List the other surfaced bids by number, let the user pick, then re-run Step 4 for that bid.
- **q** — Stop.

## Step 6 — Dashboard Nudge

Before exiting (either on `q`, or after the user says `Y` to a recommendation), print:

> Want a visual overview? Run `/ailtir_dashboard` — the same phase/next-action info is shown per bid, colour-coded.

Only print this nudge once per session (track by session, not per bid).

## State Contract — YAML Frontmatter on Bid README

Every `Bids/<BID>/README.md` grows this machine-readable header. The conductor rewrites it; other skills append `completed[]` entries via `scripts/update_frontmatter.py`.

```yaml
---
schema_version: 1
bid_id: 2026-014-CorkLibrary
project_name: Cork Library
client: Cork County Council
phase: pre-bid            # opportunity | pre-bid | estimating | submission | post-tender | delivery | closed
status: active            # active | paused | won | lost | no-bid | archived
next_action:
  skill: ailtir_compliance-matrix
  reason: "ITT uploaded; returnables not extracted yet"
  blocking: false
completed:
  - {skill: ailtir_project-indexer, at: 2026-07-02}
  - {skill: ailtir_go-no-go, at: 2026-07-02, result: proceed}
blockers: []              # e.g. [{type: rfi, ref: RFI-003, description: "Awaiting drawings"}]
key_dates:
  submission: 2026-08-15
auto_drive: false         # opt-in per-bid escalation to auto-chain (post-MVP)
---
```

## Anti-Patterns

- DO NOT chain slash commands. In Cowork the conductor recommends and the user invokes.
- DO NOT rewrite the whole README — the frontmatter block sits above the existing `# {bid_id}` heading and prose.
- DO NOT recommend a skill that is already in `completed[]` with `result: proceed` or better. Skipped skills can be re-recommended if the user changes their mind (they must explicitly ask).
- DO NOT invent phases. Phases come from `references/phase-map.md` only.
- DO NOT run the conductor if `Context/profile.json` is missing. Direct the user to `ailtir_setup`.

## Quality Checks

- [ ] `Context/profile.json` read; skill exits gracefully if missing.
- [ ] Every bid under `Bids/` has YAML frontmatter after Step 2 (either pre-existing or backfilled).
- [ ] `next_skill` recommendation matches `references/phase-map.md` for the bid's current phase.
- [ ] Blockers, if any, override the phase-canonical next skill.
- [ ] Dashboard nudge printed exactly once per session.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
