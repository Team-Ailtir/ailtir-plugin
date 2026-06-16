---
name: ailtir-project-indexer
description: Index a construction project folder into three reusable markdown context files (CLAUDE.md, project.md, and drawings.md) so future sessions can reason about the project from cheap text instead of re-parsing PDFs every time. Triggered by /ailtir-cowork-plugin:project-indexer, or during bid-planner execution.
user-invocable: false
disable-model-invocation: true
---

# Project Indexer

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" ailtir-project-indexer >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" ailtir-project-indexer > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" ailtir-project-indexer >nul 2>nul
```

Transforms a construction project folder into three durable markdown context files that downstream Claude sessions can read cheaply, instead of repeatedly re-parsing PDFs, specifications, and drawings.

## Why this skill exists

In Cowork and other long-running Claude environments, a construction project folder typically contains hundreds of PDFs — contracts, specifications, drawings, correspondence, registers. Every time Claude needs to answer a question about the project, it ends up re-opening and re-analysing drawings and documents, burning tokens and slowing everything down.

This skill does that analysis **once** and writes the result to three markdown files. After that, downstream sessions can answer most questions by reading plain text — dropping to PDF-level analysis only when they need a specific detail the markdown didn't capture.

## What gets produced

Always produce:
- **`CLAUDE.md`** — Folder structure guide. Explains what the project is, what's in each folder, and where Claude should look for what. Acts as the entry point / table of contents.
- **`project.md`** — Synthesised project summary. Pulls the important information from every non-drawing document into one narrative reference.

Produce only if drawings are present:
- **`drawings_split/`** — One single-sheet PDF per drawing sheet. Durable artefacts so downstream skills (e.g. `construction-takeoff`) can target a specific sheet without re-splitting.
- **`drawings/`** — One `.md` file per drawing sheet, each an exhaustive description of that sheet from the chosen perspective (see Step 5).
- **`drawings.md`** — Combined drawing register and index, linking to each per-sheet `.md` file in `drawings/`.

All outputs go in `Bids/[BID]/0. AI Context/`. The project root is ALWAYS the specific bid folder inside `Bids/` (e.g., `Bids/2026-004-ProjectName/`). Create the `0. AI Context/` folder if it doesn't exist.

## Workflow

Follow these steps in order. Show the user what you're doing at each step — especially the folder tree and the PDF classification — so they can catch problems before you spend tokens on drawing analysis.

### Step 1 — Discover the project

Walk the project root and build a complete inventory. Use `scripts/discover.py`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/ailtir-project-indexer/scripts/discover.py" "<project_root>" -o /tmp/project_inventory.json
```

This produces a JSON inventory listing every file, its size, its folder, and (for PDFs) quick stats that help classify it as a drawing vs a document.

**Do not assume** the folder structure follows any particular convention. The user's folders may be `1. Contract / 2. Drawings / 3. Site` or `Admin / Design / Construction` or anything else. Read whatever is there.

Show the user the folder tree and a short summary (e.g. "Found 142 PDFs across 7 top-level folders, of which 38 look like drawings") before proceeding.

### Step 2 — Classify each PDF

For every PDF, decide whether it's a **drawing** or a **document**. Use `scripts/classify.py`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/ailtir-project-indexer/scripts/classify.py" /tmp/project_inventory.json -o /tmp/project_classified.json
```

The classifier uses vector statistics (page orientation, line count, text density, aspect ratio) to split drawings from documents. It's fast and local — no vision calls. Borderline cases get flagged for human confirmation.

Show the user:
- How many PDFs were classified as drawings vs documents
- Any borderline cases the classifier is unsure about
- Ask them to confirm or override before proceeding

This is the cheapest possible point to correct mistakes. A misclassified spec sheet that gets analysed as a drawing wastes far more tokens downstream than a 10-second confirmation now.

### Step 3 — Produce CLAUDE.md (always)

CLAUDE.md is a navigation guide. It should be short enough for Claude to always keep in context when opening the project. Aim for under 300 lines.

Required sections:

```markdown
# [Project Name] — Claude Context Guide

## About this project
[2–4 sentence description inferred from folder names and key documents]

## Folder structure
[Tree of top-level folders with 1-line description of what each holds]

## Where to find what
[Mini-index: for common questions, which file/folder to consult]
- Contract terms & conditions → `2. Contract/...`
- Drawings (architectural/structural/services) → `...`
- Latest programme → `...`
- RFIs, variations, transmittals → `...`

## Related context files
- `project.md` — full project summary from all documents
- `drawings.md` — per-drawing breakdown (if present)

## Notes for Claude
- This index was generated on [date]
- The user's project conventions: [anything distinctive observed]
```

Infer the project name from folder names, the most prominent document titles, or ask the user if genuinely unclear.

### Step 4 — Produce project.md (always)

For each non-drawing PDF, read it (use `scripts/read_pdf.py` or the `pdf-reading` skill if dealing with scanned content) and extract what matters. Then synthesise everything into a single narrative summary.

**Do not just concatenate document summaries.** Group by topic, resolve contradictions, surface the important information. Use your judgment about what matters — but cover, where evidence exists in the documents:

- **Project overview** — who (client, head contractor, principal consultants), what (building type, scope, value if stated), where (address, site details)
- **Contract** — form of contract, key commercial terms, identified risks, unusual amendments, principal's project requirements
- **Scope** — what is being built; inclusions and exclusions as documented
- **Programme & key dates** — start, finish, practical completion targets, major milestones
- **Commercial position** — contract sum, approved variations, claims status, retention, superintendent's determinations (if correspondence is in the folder)
- **Open items** — outstanding RFIs, unresolved variations, pending approvals, overdue submittals
- **Site conditions & constraints** — access, hours, environmental, heritage, services, neighbours — anything operationally relevant
- **Anything else material** — unusual specifications, novated packages, long-lead items, known disputes

Use clear markdown headers. Reference source documents where it aids traceability ("per Specification 03300 §4.2"). Do not invent information; if something would normally appear in a project brief but isn't in the folder, say so briefly.

This file can be long — 2,000+ lines is fine if the project warrants it. It exists to replace re-reading 50+ PDFs.

### Step 5 — Produce drawings (if drawings exist)

Only run this step if Step 2 identified drawings.

This step has three sub-steps that **must be done in order**: (a) decide perspective, (b) split every drawing PDF into individual single-sheet PDFs, (c) analyse each sheet exhaustively and produce one `.md` per sheet plus a combined index.

#### Step 5a — Decide the analysis perspective

Drawing analysis is tuned to a **trade perspective**. A general contractor cares about everything; an electrical estimator wants electrical depth and only contextual notes on the rest; a hydraulic estimator wants hydraulic depth, etc. The perspective drives what gets emphasised in every per-sheet write-up.

Do both of the following before asking the user:

1. **Infer the likely perspective from project context.** By this point you've already read the non-drawing PDFs for `project.md`. Use that. Look at:
   - The folder name (e.g. "Pamment Electrical Tender")
   - The contract / scope documents — is this a head-contract scope or a single-trade subcontract scope?
   - The trade-specific specifications present (e.g. only Section 26 = electrical)
   - The drawing disciplines present (electrical-only set vs full multi-discipline set)

2. **Then ask the user** for confirmation and any additional context. Frame it like:

   > "Based on the project docs this looks like an **[inferred trade]** estimate / scope. I'll analyse all drawings exhaustively but focus the lens on **[inferred trade]** scope. Confirm the perspective, or override (GC, electrical, hydraulic, mechanical, structural, civil, fire, communications, etc.). Anything else I should know about scope or focus?"

Record the chosen perspective. It goes in `CLAUDE.md` and at the top of `drawings.md` so downstream sessions know how the analysis was framed.

**All drawings get analysed exhaustively regardless of trade.** A non-GC perspective doesn't mean skipping off-trade sheets — it means analysing every sheet in full, with the lens tilted toward how the chosen trade will use it. For an electrical estimator: an architectural plan is still analysed in full, but with attention on ceiling types (relevant to fixture mounting), wall constructions (relevant to chasing/penetrations), slab thicknesses (relevant to floor boxes), ceiling space coordination, etc.

#### Step 5b — Split every drawing PDF into single-sheet PDFs

Run `scripts/process_drawing.py` against every drawing PDF, sending output into `0. AI Context/drawings_split/<source_stem>/`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/ailtir-project-indexer/scripts/process_drawing.py" "<drawing_path>" \
  -o "<project_root>/0. AI Context/drawings_split/<source_stem>" \
  --dpi 200
```

For each input PDF this produces, per page:
- `<stem>_sheet<N>.pdf` — durable single-sheet PDF (kept; this is the persistent artefact)
- `<stem>_sheet<N>.png` — high-DPI render for vision analysis (used in 5c)
- `<stem>_sheet<N>.json` — extracted text and title-block hints (used in 5c)

Plus a `manifest.json` summarising the split.

**Why split first, before analysis?**
- It's deterministic and cheap. Doing it as a discrete step means a partial run can be resumed.
- Downstream skills (especially `construction-takeoff`) can target an individual sheet PDF without re-splitting.
- It makes the per-sheet `.md` files traceable to a concrete single-sheet PDF.

#### Step 5c — Exhaustive per-sheet analysis

For each sheet (using its PNG render + JSON extraction as inputs), produce a dedicated `.md` file in `0. AI Context/drawings/`. Filename convention: `<sheet_id>.md` where `<sheet_id>` is the sheet number from the title block (e.g. `A-101.md`, `E-201.md`). If the sheet ID can't be read, fall back to `<source_stem>_sheet<N>.md`.

The analysis must be **exhaustive** — the goal is that a downstream session can answer almost any question about that sheet from the `.md` alone, only opening the PDF for fine-grained spatial detail. Capture every one of the following that's present on the sheet:

**Identification**
- Sheet ID, title, discipline, scale(s), revision, revision date, drawn-by, checked-by, approval status
- Source single-sheet PDF path (link to `drawings_split/...`)
- Sheet number within the originating multi-sheet file (e.g. "sheet 4 of 12 of E-Series.pdf")

**View and content (prose, exhaustive)**
- Plan / section / elevation / detail / 3D — describe what view(s) are present
- For plans: every room, zone, area, grid reference shown. Walk the sheet zone by zone.
- For sections / elevations: levels shown, building elements depicted, what's foreground vs background
- For details: what assembly is being detailed, scale of the detail, relationship to parent sheet

**Systems and elements present**
- Every system represented (structural frame, stormwater, sanitary drainage, cable trays, ductwork, sprinklers, fire mains, comms cabling, etc.)
- For each system: routes, terminations, equipment locations, panel/board locations

**Materials and specifications called out on the sheet**
- Every material, grade, size, manufacturer, model number named on the sheet
- Don't infer materials that aren't named — note the gap if a critical material is missing
- Reference any spec section the sheet points to (e.g. "Refer Spec 26 05 19")

**Schedules and tables on the sheet**
- Type of schedule (door, window, fixture, panel, cable, fixture, finishes, equipment, etc.)
- Number of rows
- Full content of small schedules (under ~20 rows). For larger schedules, summarise structure and note row count; downstream sessions can open the PDF.

**Annotations, notes, and callouts (every one)**
- General notes verbatim or near-verbatim
- Construction notes
- Detail bubbles and what each refers to
- Dimension callouts of significance (clearances, FFL, RL, key setouts) — note them but do not attempt full dimensional takeoff
- Hold points, inspection points, NATA / authority requirements flagged on the sheet

**Cross-references**
- Every other sheet this drawing refers to (and what for)
- Every spec section referenced
- Any RFIs, variations, or revision clouds present and what they relate to

**Trade-perspective lens (drives emphasis throughout the write-up)**

Surface implications for the chosen trade even when the sheet is off-trade. Examples:

- *Electrical perspective on an architectural plan:* call out ceiling types (T-bar vs set plaster vs exposed soffit) for fixture mounting, wall constructions for chasing, joinery locations for under-cabinet lighting, accessible roof spaces, riser locations, slab thicknesses where penetrations matter.
- *Hydraulic perspective on a structural plan:* call out slab thicknesses and reinforcement zones (penetration coordination), set-downs in wet areas, riser shafts, slab edge conditions for floor wastes.
- *Mechanical perspective on an architectural section:* call out ceiling space depth, plant room volumes, riser sizes, intake/exhaust locations, AHU access.
- *Structural perspective on civil drawings:* foundation interfaces, retaining wall / slab connections, level transitions.
- *GC perspective on any sheet:* coverage is even across all trades; identify scope of works, programme drivers, sequence dependencies, interface risks.

State the perspective explicitly at the top of each per-sheet `.md` so the framing is obvious.

**Quantities — explicitly skipped**

> "Quantities are NOT extracted in this skill. For takeoffs, run the `construction-takeoff` skill against `drawings_split/<...>/<sheet>.pdf`."

Trying to count things here is unreliable and wastes tokens.

#### Step 5d — Combined drawings.md index

After all per-sheet files are written, produce `drawings.md` as an **index**, not a duplicate. It should contain:

1. Header noting the analysis perspective and date
2. The drawing register table (Sheet ID, Title, Discipline, Rev, Date, link to per-sheet `.md`)
3. A short discipline-by-discipline list with one-line summaries linking to each per-sheet `.md`

Aim to keep `drawings.md` itself short (under ~500 lines for most projects). The depth lives in the per-sheet files.

### Step 6 — Write outputs and summarise

Create the `0. AI Context/` folder at the project root (`Bids/[BID]/0. AI Context/`). Inside it, ensure these exist:

- `CLAUDE.md`
- `project.md`
- `drawings_split/` (if drawings) — one subfolder per source drawing PDF, each containing single-sheet PDFs + rendered PNGs + JSON
- `drawings/` (if drawings) — one `.md` per sheet
- `drawings.md` (if drawings) — index file

Give the user a final summary:
- Files written and their paths
- PDF count processed (documents / drawings)
- Sheet count split out of multi-page drawing PDFs
- Analysis perspective used (e.g. "Electrical estimator")
- Any PDFs that failed to parse and need their attention
- Approximate token savings on future reads (CLAUDE.md + project.md + drawings.md size vs the source docs)

## Important constraints

- **No quantity extraction from drawings.** Describe what's there; don't count. Point users at `construction-takeoff` for that — it can target the per-sheet PDFs in `drawings_split/`.
- **Split drawings to PDF first, analyse second.** The single-sheet PDFs in `drawings_split/` are durable artefacts that must be persisted before per-sheet analysis begins. A partial run can then resume mid-way.
- **Always confirm the analysis perspective before Step 5c.** Inferring is fine; assuming silently is not. Record the chosen perspective in `CLAUDE.md` and at the top of `drawings.md`.
- **All sheets get exhaustive analysis regardless of perspective.** Off-trade sheets aren't skipped — they're analysed in full with the lens tilted toward the chosen trade.
- **Don't invent information.** If a document or drawing doesn't say something, don't fill it in from assumption. Note the gap briefly.
- **Preserve folder numbering conventions.** If the user's folders are `1. / 2. / 3.`, call the output folder `0. AI Context/` to sort first. If they're not numbered, just use `AI Context/`.
- **Run classification before drawing analysis.** Vision-on-PDF is the expensive step. Make sure the user has signed off on the drawing list before you start that loop.
- **Index incremental-friendly.** If `0. AI Context/` already exists with prior outputs, read them first. For re-runs, only re-process PDFs whose modified-date is newer than the last index, or that weren't previously indexed. Offer this to the user rather than always doing a full rebuild.

## Re-running the skill

If the user triggers this skill on a folder that's already been indexed (0. AI Context/ exists with outputs):

1. Read the existing CLAUDE.md to see when it was last generated
2. Compare the file inventory from Step 1 against the prior run
3. Ask the user: "This project was indexed on [date]. I can (a) rebuild from scratch, or (b) update incrementally — only reprocess new or modified files." Default to (b) unless they say otherwise.

- [HUMAN INPUT REQUIRED] Before starting drawing analysis (Step 5c), confirm the analysis perspective with the user.

## Anti-Patterns (What NOT to do)
- DO NOT skip the OCR step for drawings. The `process_drawing.py` script is mandatory for PDFs.
- DO NOT overwrite existing files without checking first.
- DO NOT hallucinate drawing numbers or titles. Extract them directly from the files.

## Reference files

- `references/output_templates.md` — Full templates and worked examples for CLAUDE.md, project.md, and drawings.md. Read this when you're ready to write each file.
- `references/classification_heuristics.md` — How the drawing vs document classifier works and how to handle edge cases.

## Scripts

- `scripts/discover.py` — Walks the project folder, produces file inventory with PDF stats.
- `scripts/classify.py` — Classifies PDFs as drawings or documents from inventory stats.
- `scripts/process_drawing.py` — For each page of a drawing PDF: writes a durable single-sheet PDF, a high-DPI PNG render, and a JSON of extracted text + title-block hints. The single-sheet PDFs live in `0. AI Context/drawings_split/` and are reusable by downstream skills (e.g. `construction-takeoff`).
- `scripts/read_pdf.py` — Small helper for reading document PDFs to text.

## Quality Checks
- [ ] All PDFs classified as drawings or documents before analysis begins.
- [ ] `0. AI Context/` folder created at `Bids/[BID]/0. AI Context/`.
- [ ] `CLAUDE.md` and `project.md` written with no hallucinated content.
- [ ] Drawing register includes every sheet with correct discipline and revision.
