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
- `plugin_version`: `2.16.0`
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

Compute `next_skill` from `references/phase-map.md` in this skill's directory. The phase map lists, for each `phase`, the expected sequence of skills — pick the earliest expected skill not present in `completed[]` (or present only with `result: summarised` — see below). If `blockers[]` is non-empty, override `next_skill` with the appropriate resolution skill (e.g. `ailtir_rfi-generator` for a `type: rfi` blocker).

**`summarised` entries:** an entry in `completed[]` with `result: summarised` (written
by `ailtir_bid-planner` for compliance and contract-risk) counts as "overview done,
deep pass still valuable". Recommend it as `next_skill` and phrase the rationale as
a deep dive — e.g. "Summarised in the bid plan; run for the full clause-by-clause
review." Treat `result: proceed` as fully complete (do not re-recommend). A
`skipped` entry is also complete, but may be re-recommended if the user explicitly
asks to revisit it.

**Intelligence/ thin-check (submission phase only):** when the bid's current `phase` is `submission`, check whether `Intelligence/` in the workspace root contains fewer than 2 `.md` or `.yaml` files (count with a glob, do not read their contents). If it does, append this line to the four-line block:

```text
Note: Intelligence/ looks thin — `/ailtir_intelligence-builder` now will improve quality-writer drafts for this submission.
```

Do not add this note outside the submission phase. Do not add it if Intelligence/ has 2 or more files.

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
  - **Show full process** — display every phase and skill in order as a human-readable walkthrough
- A **Submit** button that writes a message back into the chat, exactly as the
  bid-planner form's submit button does. **The message text depends on the
  selected card:**
  - **Run it** → write the bare slash command for **this bid's computed
    `{next_skill}`** — the value you determined in Step 4 from
    `references/phase-map.md` for the surfaced bid, whatever it is
    (`/ailtir_go-no-go`, `/ailtir_takeoff`, `/ailtir_contract-risk`, …). Never
    hardcode one skill; always substitute the actual `{next_skill}` for the bid
    being prompted. Write only that command, nothing else. This posts as a user
    command, so Cowork runs the skill directly. Do **not** write
    `conductor: run it`; that is a plain message the conductor cannot act on.
  - Every other card → write `conductor: <action>` (e.g. `conductor: defer`,
    `conductor: skip`, `conductor: explain`, `conductor: pick another`,
    `conductor: quit`, `conductor: show process`). The conductor reads that on the next turn and runs the
    matching action below.
  - **Show full process** → write `conductor: show process`

Keep the cards visually consistent with the bid-planner style: bordered cards,
icon or bold title, muted description line, dark-theme friendly.

Handle the submitted message:

- **`/{next_skill}` (Run it)** — nothing for the conductor to do; the skill has
  been invoked directly. It will run on `{bid_path}`. When it finishes the user
  re-runs `/ailtir_conductor` to see what's next.
- **`conductor: defer`** — Run `scripts/update_frontmatter.py --bid-path <path> --set next_action.reason "Deferred by user on {today}"`. Move to the next bid.
- **`conductor: skip`** — Ask why briefly, then run `scripts/update_frontmatter.py --bid-path <path> --skip {next_skill} --reason "<user's reason>"`. The skill gets appended to `completed[]` with `result: skipped`. Move on.
- **`conductor: explain`** — Read the relevant paragraph from `references/skill-catalogue.md` in this skill's directory, print it, then re-present the Step 5 card.
- **`conductor: pick another`** — List the other surfaced bids by number, let the user pick, then re-run Step 4 for that bid.
- **`conductor: quit`** — Stop.
- **`conductor: show process`** — Read `references/phase-map.md` from this skill's directory. Render the full phase sequence as a clean human-readable walkthrough using this format:

  ```text
  The Ailtir Bid Lifecycle — Full Process

  PHASE: opportunity
    1. /ailtir_go-no-go — score the opportunity; proceed or no-bid

  PHASE: pre-bid
    1. /ailtir_bid-planner — Tier-1 first pass: workbook + deck, full Go/No-Go, summarised risk & compliance, package outline
    2. /ailtir_contract-risk — full clause-by-clause risk register (deep dive)
    3. /ailtir_compliance-matrix — full returnables tracker (deep dive)
    4. /ailtir_pqq-manager — PQQ / SQ / Supplier Info form (if required)

  PHASE: estimating
    1. /ailtir_package-breakdown — define trade packages
    2. /ailtir_takeoff — quantities from drawings → NRM2 register
    3. /ailtir_subcontractor-enquiry — issue ITT letters per package
    4. /ailtir_prelims-builder — priced prelims schedule
    5. /ailtir_bid-leveling — normalise sub quotes
    6. /ailtir_cost-reconciliation — final gap/benchmark check

  PHASE: submission
    1. /ailtir_quality-writer — draft written responses
    2. /ailtir_programme-builder — tender programme + narrative
    3. /ailtir_bid-assembly — compile the master submission
    4. /ailtir_submission-preflight — compliance check before send

  PHASE: post-tender
    1. /ailtir_post-tender-interview — (if invited to interview)
    2. /ailtir_case-study-generator — debrief capture + case study seed
    3. /ailtir_feedback — 1–10 bid experience rating

  PHASE: delivery
    1. /ailtir_site-diary — daily records
    2. /ailtir_contract-admin — delay, CE, L&E event records

  Support skills (available at any time, not sequenced):
    /ailtir_rate-library, /ailtir_rfi-generator, /ailtir_intelligence-builder
  ```

  After printing the walkthrough, re-present the Step 5 card for the current bid so the user can act immediately.

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
  skill: ailtir_contract-risk
  reason: "Summarised in the bid plan; run the full clause-by-clause review"
  blocking: false
completed:
  # result values: proceed (done in full) | summarised (bid-planner overview,
  # deep dive still worthwhile) | skipped (deliberately not done)
  - {skill: ailtir_bid-planner, at: 2026-07-02, result: proceed}
  - {skill: ailtir_go-no-go, at: 2026-07-02, result: proceed}
  - {skill: ailtir_compliance-matrix, at: 2026-07-02, result: summarised}
  - {skill: ailtir_contract-risk, at: 2026-07-02, result: summarised}
blockers: []              # e.g. [{type: rfi, ref: RFI-003, description: "Awaiting drawings"}]
key_dates:
  submission: 2026-08-15
auto_drive: false         # opt-in per-bid escalation to auto-chain (post-MVP)
---
```

## Anti-Patterns

- DO NOT write the fully-qualified `/ailtir-cowork-plugin:ailtir_<name>` form anywhere the user sees it. Cowork invokes skills as `/ailtir_<name>` — always use that short form in cards, messages, and prose. Never expand it back to the plugin-namespaced form.
- DO NOT make the "Run it" card write a plain sentence or `conductor: run it`. It must write the bare slash command `/{next_skill}` so Cowork runs the skill directly.
- DO NOT hardcode a specific skill in the "Run it" card. `{next_skill}` is recomputed per bid in Step 4 — the card must always carry the skill that is actually next for the bid being prompted, for every phase and every bid.
- DO NOT chain slash commands from inside the skill. The "Run it" card works because the *user's* submitted message is the slash command, not because the conductor invokes it.
- DO NOT rewrite the whole README — the frontmatter block sits above the existing `# {bid_id}` heading and prose.
- DO NOT recommend a skill that is already in `completed[]` with `result: proceed`. An entry with `result: summarised` is NOT complete — recommend it as a deep dive (see Step 4). Skipped skills can be re-recommended if the user explicitly asks.
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
