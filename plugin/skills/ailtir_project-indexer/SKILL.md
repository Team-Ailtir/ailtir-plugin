---
name: ailtir_project-indexer
description: Index a construction project folder into three reusable markdown context files (CLAUDE.md, project.md, and drawings.md) so future sessions can reason about the project from cheap text instead of re-parsing PDFs every time. Triggered by /ailtir-cowork-plugin:ailtir_project-indexer, or during bid-planner execution.
---

# Project Indexer

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_project-indexer`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

This skill turns a bid folder — the atomic unit of Ailtir's estimating pipeline —
into a durable set of markdown context files. Once produced, every downstream
Ailtir skill that touches the same bid can reason from plain text rather than
paying the vision and parsing cost of the source PDFs on every invocation.

## Why this skill exists

An Ailtir bid folder holds a small mountain of PDFs: tender correspondence,
employer's requirements, specifications, drawing sets, the form of contract,
prelims documents, and structured registers. The Cowork plugin then runs seven
or eight skills against that same pack — `ailtir_bid-planner`,
`ailtir_go-no-go`, `ailtir_compliance-matrix`, `ailtir_estimating-workflow`,
`ailtir_contract-risk`, `ailtir_prelims-builder`, and others — each asking
broadly similar questions of the tender. If every skill re-opens the PDFs on
its own, token spend balloons and answers drift.

`ailtir_project-indexer` pays that parse cost once and writes the digested
result to disk. Every subsequent bid-scoped skill can then load cheap markdown
instead. The generated files also carry the **active profile** (`ireland-gc`
or `uk-gc`) and the chosen **trade perspective**, so profile-specific
compliance framing and trade-specific emphasis persist across sessions.

## What gets produced

Every output lands inside `Bids/{BID}/0. AI Context/`. The `0.` prefix keeps
the AI context folder at the top of Ailtir's numbered bid layout.

- `CLAUDE.md` — short navigation guide. Names the bid, the active profile,
  the trade perspective, the top-level folder layout, and a lookup table
  pointing the model at the right file for common questions.
- `project.md` — long-form narrative synthesising every non-drawing PDF,
  organised by topic rather than by source.
- `drawings.md` — drawing register and index (only when drawings exist).
- `drawings/<sheet_id>.md` — one exhaustive per-sheet analysis. Named from
  the title-block sheet ID where readable (e.g. `A-101.md`), otherwise the
  source stem plus page number.
- `drawings_split/<source_stem>/…` — durable single-sheet artefacts (PDF +
  PNG + JSON) per page, consumed later by `ailtir_takeoff`.

Templates for each output live in `references/output_templates.md`; that
file also holds worked examples for both profiles.

## Workflow

Six steps, in the order below. Show your reasoning as you go — the folder
tree after Step 1 and the classification result after Step 2 are the two
cheapest points to correct a mistake before drawing analysis consumes real
tokens.

### Step 1 — Inventory the bid

Run `scripts/discover.py <bid_root> -o /tmp/project_inventory.json` under
`python3`. The helper walks the tree and pulls quick statistics from each
PDF (page count, orientation, approximate ISO 216 sheet size, text density)
so the next step can classify without reopening files.

Do not assume the folder layout. Ailtir bids are typically numbered
(`1. Brief`, `2. Contract`, `3. Drawings`, …) but tender packs often arrive
as an unstructured dump. Print the tree and a short summary to the user —
total PDF count, provisional drawing/document counts, any files that failed
to open — and wait for acknowledgement before continuing.

### Step 2 — Classify PDFs

Run `scripts/classify.py /tmp/project_inventory.json -o /tmp/project_classified.json`
under `python3`. The classifier scores each PDF against a suite of signals:
ISO 19650 filename fields (see `research/drawing-conventions.md` for the
convention), page media-box size against the ISO 216 A-series, orientation,
text-to-vector ratio, and title-block hints. Every PDF is labelled
`drawing`, `document`, or `unsure`.

Present the outcome to the user:

- Totals per class.
- The full list of `unsure` items with the top two competing scores and the
  reason each was assigned.
- Any file whose ISO 19650 `Type` field (e.g. `DR` for drawing) contradicts
  the vector-based classification — these are the highest-value confirmations.

Confirm or override every borderline case before proceeding. This is the
last cheap correction point; a spec sheet that survives here as a drawing
will burn vision tokens for no gain, and a drawing misfiled as a document
will never appear in the register.

### Step 3 — Synthesise the document narrative

For each PDF classified as a document, extract the text with
`scripts/read_pdf.py`. If the helper exits with the image-only code, fall
back to the `pdf-reading` skill or invite the user to supply an OCR pass —
scanned tender packs are common on legacy jobs.

Then produce two files together, because they share source material:

- `CLAUDE.md`, kept under 300 lines. It is the navigation index and it
  should fit comfortably in context alongside any downstream skill's own
  prompt. Include the bid identifier, the active profile from the bid
  README frontmatter, a compact tree of the top-level folders with one
  line per folder, and a lookup table for the questions Ailtir skills
  routinely ask ("form of contract", "employer's requirements", "latest
  drawing register", "programme").
- `project.md`, as long as the bid warrants. Group findings by topic
  (contract, scope, programme, commercial position, site constraints,
  outstanding items, unusual specifications), not by source PDF. Where the
  active profile is `ireland-gc`, surface RIAI/GCCC-specific clauses;
  where it is `uk-gc`, surface JCT/NEC-specific clauses. Cite source
  documents inline for traceability. If a topic that would normally
  appear in a tender brief is silent, say so — do not invent.

Use the templates in `references/output_templates.md` verbatim as the
starting shape for both files.

### Step 4 — Confirm the trade perspective

Decide the lens for drawing analysis before any sheets are opened. A GC
bid on a full multi-discipline pack calls for even coverage; a subcontract
bid — electrical, mechanical, groundworks — wants that trade's depth on
every sheet, off-trade sheets included.

Infer first, from what Step 3 already surfaced: the bid folder name, the
scope documents, which specification sections are present (Section 26
only vs full NBS coverage), which drawing disciplines the Step 2 register
hints at, and any explicit statement in the invitation to tender.

Then confirm with the user. Frame the question with your inferred answer
so it can be accepted in one word, and offer the override list (GC,
architectural, structural, civil, mechanical, electrical, hydraulic /
public health, fire, communications, groundworks, external works). The
vision tokens spent in Step 5b are the biggest single cost in the
workflow — silent inference is not acceptable.

The chosen perspective is recorded in `CLAUDE.md`, at the top of
`drawings.md`, and at the top of every per-sheet analysis.

### Step 5 — Drawing pipeline

Only run this step if Step 2 found drawings. It has three sub-steps that
must run in order.

#### Step 5a — Split every drawing PDF

For each drawing PDF, run `scripts/process_drawing.py <pdf> -o "<bid_root>/0. AI Context/drawings_split/<source_stem>" --dpi 200`
under `python3`. Per input page the helper writes:

- `<stem>_sheet<N>.pdf` — the durable single-sheet artefact. Kept
  permanently and consumed later by `ailtir_takeoff` when quantities are
  needed.
- `<stem>_sheet<N>.png` — a 200-DPI render for vision analysis in Step 5b.
- `<stem>_sheet<N>.json` — extracted text plus ISO 19650 title-block hints
  (sheet ID, discipline role code, revision, suitability, scale, sheet
  size against ISO 216).

Every source PDF also produces a `manifest.json` naming the sheets it
split into. The split is deterministic, so partial runs resume cleanly:
if the process is interrupted after five drawings, the sixth is the only
one that needs redoing.

#### Step 5b — Analyse each sheet exhaustively (parallel sub-agents)

Dispatch the plugin-scoped `drawing-analyst` sub-agent via the `Agent`
tool, one invocation per sheet. Sub-agents run in isolated context
windows: vision tokens for each sheet stay inside the sub-agent, and
only a compact JSON status returns to this skill. The Cowork runtime
schedules up to 16 concurrent sub-agents and queues the rest, so a
30-sheet pack that used to walk sheet-by-sheet in this main context
now completes in two rounds without polluting the main window.

For each single-sheet artefact produced by Step 5a, decide the target
filename first: use the sheet ID from `<stem>_sheet<N>.json`
(`title_block.hints.sheet_number`), fall back to
`<source_stem>_sheet<N>.md` when the title block was unreadable. Then
invoke `drawing-analyst` with these fields (all absolute paths):

- `png_path` — `<bid_root>/0. AI Context/drawings_split/<stem>/<stem>_sheet<N>.png`
- `json_path` — `<bid_root>/0. AI Context/drawings_split/<stem>/<stem>_sheet<N>.json`
- `pdf_path` — `<bid_root>/0. AI Context/drawings_split/<stem>/<stem>_sheet<N>.pdf`
- `output_path` — `<bid_root>/0. AI Context/drawings/<sheet_id>.md`
- `trade_perspective` — the value confirmed in Step 4
- `active_profile` — from `Context/profile.json`
- `bid_ref` — the bid folder name

Dispatch every sheet in one batch — do not throttle manually. The
runtime handles concurrency. Every ~25 returned statuses, print a
one-line progress note to the user ("Analysed 25 of 78 sheets") so
long runs stay visible.

Collect each sub-agent's returned JSON status. The array feeds Step 5c's
register (sheet ID, discipline, revision, suitability, revision date,
one-line summary) and Step 6's handover (gaps, sheets flagged for
manual review).

Failure handling (Cowork v2.1.199+ returns structured failure signals
rather than error text as findings):

- If a sub-agent's returned status is a failure signal (API error,
  usage limit, repeated server error), retry that single sheet once.
- If the retry also fails, keep whatever `.md` the sub-agent wrote
  before termination and add the sheet to the Step 6 "manual review"
  list. Do not treat error text as sheet content.
- If a returned JSON is malformed (not parseable, missing required
  fields), treat it as a failure and follow the same retry-once path.

Quantities remain out of scope for the drawing-analyst. Counts,
lengths, and areas are `ailtir_takeoff`'s responsibility — that skill
runs against the same single-sheet PDF in `drawings_split/` and
produces auditable results.

#### Step 5c — Combined register

After every per-sheet file is written, produce `drawings.md`. It is an
index, not a re-statement of the per-sheet content. Include:

- A header naming the trade perspective, the active profile, and the
  generation date.
- The drawing register table: sheet ID, discipline (from the ISO 19650
  role code), title, latest revision, latest suitability, issue date,
  and a relative link to the per-sheet `.md`.
- A short discipline-by-discipline summary — one line per sheet under
  each discipline heading, each linking to the per-sheet file.

Aim to keep `drawings.md` itself under 500 lines. The depth lives in the
per-sheet files.

### Step 6 — Handover

Confirm the `0. AI Context/` folder now contains everything expected:
`CLAUDE.md`, `project.md`, `drawings.md` (if drawings), `drawings/`
(if drawings), `drawings_split/` (if drawings). Then produce a summary
for the user:

- Paths of every top-level output file written.
- Counts: PDFs processed, documents synthesised, drawings split, sheets
  analysed.
- Active profile and trade perspective.
- Any files that failed to parse and need manual attention.
- Approximate token savings for downstream skills — the combined size of
  `CLAUDE.md` + `project.md` + `drawings.md` against the aggregate size
  of the source PDFs.

Then run the two completion patterns at the tail of this file: update
the bid README frontmatter via the Soul-Update pattern, and recommend
the next skill from the conductor phase-map.

## Important constraints

- **No quantities from drawings in this skill.** If a downstream question
  needs a count, a length, or an area, invoke `ailtir_takeoff` against
  the appropriate `drawings_split/<stem>/<sheet>.pdf`.
- **Split before analyse.** The single-sheet PDFs must be on disk before
  any per-sheet write-up begins. A partial run then resumes from the
  first unprocessed sheet.
- **Perspective is confirmed, not assumed.** Silent inference is banned
  before Step 5b; the vision spend justifies the one-line question.
- **Every sheet is analysed in full.** Off-trade sheets are not
  skipped; they are analysed exhaustively through the chosen trade's
  lens.
- **Never invent.** If a document or a sheet does not say something, note
  the gap. Do not fill it from prior projects or from assumption.
- **Preserve Ailtir folder numbering.** Ailtir bids use numbered
  top-level folders; the AI context folder is `0. AI Context/` so it
  sorts to the top. Do not rename or reorder existing bid subfolders.
- **Never read from `.competitor-reference-quarantine/`.** That path is
  reserved for legally quarantined material and must not appear in any
  input list, prompt, or reference.
- **Incremental by default on re-runs.** If `0. AI Context/` already
  exists, only reprocess what has changed since the last generation.
- **Respect the ISO 19650 status distinction.** A sheet at S0–S4 is not
  for construction; a sheet at A1+ is. Record the code, and do not treat
  a preliminary issue as if it were contractual.

## Re-running the skill

If `0. AI Context/` already exists in the bid folder when this skill is
triggered:

1. Read the existing `CLAUDE.md` to find the previous generation date and
   the previous file inventory.
2. Compare the current Step 1 inventory against the prior one. Identify
   new PDFs, modified PDFs (modification time newer than the CLAUDE.md
   timestamp), and PDFs removed since the last run.
3. Present the diff to the user and offer two paths: (a) incremental
   update — process only the changed set, refreshing `project.md` and
   the register in place; or (b) full rebuild — regenerate everything
   from scratch. Default to (a) unless the user requests otherwise.
4. Full rebuild is still the right choice when the trade perspective or
   the active profile has changed since the last run — both change what
   the drawing analysis should emphasise.

- [HUMAN INPUT REQUIRED] Confirm the trade perspective at Step 4 before
  drawing analysis starts.

## Anti-Patterns (What NOT to do)
- DO NOT skip the OCR step for drawings. The `process_drawing.py` script is mandatory for PDFs.
- DO NOT overwrite existing files without checking first.
- DO NOT hallucinate drawing numbers or titles. Extract them directly from the files.

## Reference files

- `references/output_templates.md` — Full templates and worked examples for CLAUDE.md, project.md, and drawings.md. Read this when you're ready to write each file.
- `references/classification_heuristics.md` — How the drawing vs document classifier works and how to handle edge cases.
- `research/drawing-conventions.md` — ISO 19650 and BS 1192 filename fields, role/type/level codes, suitability and revision codes, RIBA stages, ISO 216 sheet sizes, title-block layout, US National CAD Standard. Consult before parsing any drawing filename or title block.

## Scripts

- `scripts/discover.py` — Walks the bid folder, produces a file inventory with PDF page count, orientation, ISO 216 sheet-size guess, and text density.
- `scripts/classify.py` — Scores each PDF as drawing vs document using ISO 19650 filename signals, vector page statistics, and title-block hints.
- `scripts/process_drawing.py` — For each page of a drawing PDF: writes a durable single-sheet PDF, a high-DPI PNG render, and an ISO 19650-aware JSON of extracted text plus title-block hints. The single-sheet PDFs are reused by `ailtir_takeoff`.
- `scripts/read_pdf.py` — Text extraction for document PDFs, with a dedicated exit code when the file is image-only and needs OCR.

## Quality Checks
- [ ] All PDFs classified as drawings or documents before analysis begins.
- [ ] `0. AI Context/` folder created at `Bids/[BID]/0. AI Context/`.
- [ ] `CLAUDE.md` and `project.md` written with no hallucinated content.
- [ ] Drawing register includes every sheet with correct discipline and revision.

## On Completion — Update Bid State

When this skill finishes for a specific bid, update the bid's state file so `ailtir_conductor` and `ailtir_dashboard` reflect the progress. Run the sibling `ailtir_conductor` skill's `scripts/update_frontmatter.py` helper with `python3`:

```
python3 <ailtir_conductor>/scripts/update_frontmatter.py \
    --bid-path Bids/<BID> \
    --complete <this skill's folder name> \
    --result proceed
```

Substitute `<BID>` for the bid folder name (e.g. `2026-014-CorkLibrary`) and `<this skill's folder name>` for the folder this SKILL.md lives in (e.g. `ailtir_project-indexer`). Use `--result skipped` and `--reason "..."` if the user asked to skip rather than complete.

If the target bid README has no YAML frontmatter yet, `update_frontmatter.py` will exit with code 3. In that case, run `scripts/init_bid_frontmatter.py` from the same sibling skill first, then retry the update.

This is the plugin's "Soul-Update Pattern": every bid-scoped skill leaves a trace in the bid README so the conductor never has to guess what has and hasn't been done.

## On Completion — Recommend the Next Step

After the frontmatter has been updated, help the user by naming what comes next — do not make them re-invoke `ailtir_conductor` just to see it.

Read `references/phase-map.md` from the sibling `ailtir_conductor` skill's directory. Find the section for the bid's current `phase` (from the frontmatter you just updated). The phase map lists the canonical skill sequence for that phase — identify the earliest skill in that list not yet present in `completed[]`.

Then print exactly this block at the very end of your response:

```text
Next up on {bid_id} ({phase} phase):
  → /ailtir-cowork-plugin:{next_skill} — {one-line rationale from the phase map}

Or run /ailtir-cowork-plugin:ailtir_conductor for a full cross-bid view.
```

Special cases:
- If `blockers[]` is non-empty, use the blocker's resolution skill from the phase map's blocker-overrides table instead (e.g. `ailtir_rfi-generator` for `type: rfi`) and lead with "Blocked — resolve first:".
- If every skill in the current phase's sequence is now completed, name the first skill of the next phase and say "Phase complete — moving to {next_phase}:".
- If the bid has reached `closed` or `delivery` with no obvious next step, print "No canonical next step — run `/ailtir-cowork-plugin:ailtir_conductor` to see the full pipeline." instead of a specific recommendation.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
