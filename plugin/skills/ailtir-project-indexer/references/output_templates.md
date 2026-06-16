# Output Templates

Load this reference when you're ready to write the three output files.
These are templates, not rigid forms — adapt sections to what the project actually contains.

---

## CLAUDE.md template

```markdown
# [Project Name] — Claude Context Guide

_Generated [YYYY-MM-DD] by project-indexer. Re-run the skill to refresh._

## About this project

[2–4 sentences: what's being built, for whom, contracting model, location.
Inferred from folder names and key documents. If unclear, say so.]

## Folder structure

```
[project root]
├── 1. Project Docs/          — [brief description of what's in here]
├── 2. Contract/              — [brief description]
├── 3. Estimate/              — [brief description]
├── 4. Correspondence/        — [brief description]
├── 5. Registers/             — [brief description]
├── 6. Programme/             — [brief description]
├── 7. Site/                  — [brief description]
└── 0. AI Context/            — generated context files (this file, project.md, drawings.md)
```

## Where to find what

Use this as a mini-index when you need a specific piece of information:

- **Head contract, GCs, amendments** → `2. Contract/`
- **Drawings** (all disciplines) → [wherever they actually live]
- **Current programme / Gantt** → `6. Programme/`
- **RFIs, variations, transmittals** → `5. Registers/`
- **Correspondence with principal/subcontractors** → `4. Correspondence/`
- **[...etc]**

## Related context files

- `project.md` — Narrative project summary synthesised from all documents. Read this before answering project-specific questions.
- `drawings.md` — Drawings index (drawing register + per-discipline list with links). Read for the lay-of-the-land.
- `drawings/<sheet_id>.md` — Per-sheet exhaustive description (one file per sheet). Read the relevant file before answering questions about a specific sheet.
- `drawings_split/<source>/<sheet>.pdf` — Single-sheet PDFs split out from multi-sheet drawing files. Use these as inputs to the `construction-takeoff` skill.

## Analysis perspective

Drawings were analysed from the **[e.g. Electrical estimator]** perspective. All sheets received exhaustive coverage; emphasis tilts toward the chosen trade. Re-run the skill with a different perspective if needed.

## Notes for Claude

- Generated [date]. Files modified after this date may not be reflected.
- For quantity takeoffs from drawings, use the `ailtir-takeoff` skill against `drawings_split/<...>/<sheet>.pdf` — this index does not contain quantities.
- For document-level specifics (e.g. exact clause wording), open the source PDF; this index summarises but doesn't reproduce.
- [Any user-specific conventions observed, e.g. "Rev letters mean A=initial issue, B=for construction"]
- **Commercial sensitivity:** This is a live tender. All pricing, margin, risk positions, and bid strategy in this folder are commercially sensitive. Do not share or export this data outside the workspace without explicit user confirmation.
```

**Keep CLAUDE.md under ~300 lines.** It's the always-read entry point; bloat defeats its purpose.

---

## project.md template

```markdown
# [Project Name] — Project Summary

_Generated [YYYY-MM-DD] from [N] documents across [N] folders._

## 1. Project overview

- **Project name:** [from documents]
- **Client / Principal:** [name]
- **Head contractor:** [name, if applicable]
- **Project manager / Superintendent:** [name]
- **Architect / Lead designer:** [name]
- **Other key consultants:** [list]
- **Address / Site:** [full address]
- **Project type:** [e.g. new-build commercial, refurbishment, civil infrastructure]
- **Approximate value:** [if stated]
- **Contracting model:** [e.g. lump sum, construct-only, D&C, ECI]

## 2. Contract

- **Form of contract:** [e.g. AS 4000-1997 as amended]
- **Contract date:** [date]
- **Contract sum:** [amount]
- **Key amendments to standard form:** [list]
- **Notable risk allocations:** [e.g. site conditions, latent, time bar provisions]
- **Security / retention:** [%]
- **Liquidated damages:** [rate, cap]
- **Defects liability period:** [months]
- **[Other clauses worth flagging]**

## 3. Scope

### Inclusions

[Bullet list of what's being built. Group by trade or building element where helpful.]

### Exclusions (as documented)

[Bullet list]

### Specification highlights

[Material / system specifications worth knowing at-a-glance, with source reference.
E.g.: "Concrete — N40, 80mm cover to reinforcement in-ground (Spec 03300 §4.2)"]

## 4. Programme & key dates

| Event | Date | Source |
|---|---|---|
| Site possession | ... | ... |
| Commencement | ... | ... |
| Practical completion | ... | ... |
| [Milestones] | ... | ... |

## 5. Commercial position

- **Contract sum:** [amount]
- **Approved variations:** [count, total $, if tracked in correspondence/registers]
- **Pending variations:** [count, total $]
- **Claims to date:** [summary if available]
- **Retention held:** [amount]
- **[Other commercial notes]**

## 6. Open items

Outstanding matters that downstream sessions should be aware of:

- [ ] [Open RFI: number, subject, raised date]
- [ ] [Pending variation: number, scope, value]
- [ ] [Overdue submittal / approval]
- [ ] [Unresolved correspondence thread]

## 7. Site conditions & constraints

- **Site access:** ...
- **Working hours:** ...
- **Environmental / heritage:** ...
- **Services:** ...
- **Neighbour constraints:** ...

## 8. Other material information

[Anything the documents surface that doesn't fit above but matters — novated packages,
long-lead items, known disputes, unusual specifications, commercial sensitivities.]

## 9. Source documents

| Document | Folder | Role |
|---|---|---|
| [filename] | [folder] | [e.g. "Head contract"] |
| ... | ... | ... |

## 10. Gaps

Information a downstream session might expect but that isn't in this folder:

- [e.g. "No current programme found — last dated 2024-08"]
- [e.g. "Contract sum inferred from priced schedule; signed form of agreement not present"]
```

---

## Per-sheet drawing template (one .md per sheet, in `drawings/`)

Each sheet gets its own `.md` file. Filename: `<sheet_id>.md` (e.g. `A-101.md`, `E-201.md`). Fall back to `<source_stem>_sheet<N>.md` if the sheet ID can't be read from the title block.

```markdown
# [Sheet ID] — [Sheet Title]

**Discipline:** [Architectural / Structural / Civil / Electrical / Hydraulic / Mechanical / Fire / Comms / Landscape / etc.]
**Revision:** [Rev letter] dated [YYYY-MM-DD]
**Scale(s):** [e.g. 1:100, details 1:20]
**Drawn / Checked / Approved:** [as shown in title block]
**Source single-sheet PDF:** `drawings_split/<source_stem>/<source_stem>_sheet<N>.pdf`
**Originating file:** `<source_stem>.pdf` — sheet [N] of [total]
**Analysis perspective:** [e.g. Electrical estimator] _(perspective drives emphasis below)_

> Quantities are NOT extracted in this file. For takeoffs, run the `construction-takeoff` skill against the source single-sheet PDF above.

## View and content

[Exhaustive prose. Walk the sheet zone-by-zone or view-by-view. For plans: every room, every grid reference, every visible system. For sections / elevations: levels, building elements, foreground vs background. For details: which assembly, scale, parent reference.]

## Systems and elements present

[Every system shown — structural frame, stormwater, sanitary drainage, cable trays, sprinklers, mechanical ducts, etc. For each: routes, terminations, equipment locations.]

## Materials and specifications called out

[Every material/grade/size/manufacturer/model named ON the sheet. Don't infer. Note the spec section the sheet points to where applicable.]

## Schedules on the sheet

[For each schedule: type, row count, structure. Reproduce small schedules (under ~20 rows) in full. Summarise larger ones — the source PDF has the rows.]

## Annotations, notes, and callouts

[General notes, construction notes, detail bubbles, key dimensional callouts (clearances, FFL, RL, key setouts), hold points, NATA/inspection requirements. Capture every annotation visible on the sheet.]

## Cross-references

- Other sheets: [list with what each is referenced for]
- Specifications: [section numbers and what they cover]
- RFIs / variations / revision clouds: [if any visible on the sheet]

## [Perspective]-relevant implications

[Trade-perspective lens. Surface implications for the chosen trade even when this sheet is off-trade. Examples:
- Electrical perspective on architectural plans → ceiling types for fixture mounting, wall constructions for chasing, joinery for under-cabinet lighting, riser locations.
- Hydraulic perspective on structural plans → slab thicknesses, set-downs, riser shafts, slab edges for floor wastes.
- Mechanical perspective on architectural sections → ceiling space depth, plant room volumes, riser sizes, intake/exhaust.
- GC perspective → even coverage; scope, programme drivers, sequence dependencies, interface risks.]

## Gaps and notes for downstream sessions

[Anything material missing from the sheet that a downstream session might reasonably expect — e.g. "No legend present; symbols not defined on this sheet." or "Cable sizes not shown — refer schedule on E-901."]
```

---

## Combined drawings.md template (index file)

The combined `drawings.md` is an **index**, not a duplicate of the per-sheet content. Keep it short — the depth lives in `drawings/<sheet_id>.md`.

```markdown
# [Project Name] — Drawings Index

_Generated [YYYY-MM-DD] from [N] drawing files ([N] sheets total)._
**Analysis perspective:** [e.g. Electrical estimator] _(applies to every per-sheet file)_

> Per-sheet exhaustive write-ups live in `drawings/<sheet_id>.md`.
> Single-sheet PDFs (durable artefacts for downstream skills) live in `drawings_split/<source_stem>/`.
> Quantities are NOT extracted. For takeoffs, run the `construction-takeoff` skill against the relevant single-sheet PDF.

## Drawing register

| Sheet | Title | Discipline | Rev | Date | Per-sheet file |
|---|---|---|---|---|---|
| A-001 | Cover Sheet | Architectural | C | 2026-03-12 | [A-001.md](drawings/A-001.md) |
| A-101 | Ground Floor Plan | Architectural | B | 2026-02-04 | [A-101.md](drawings/A-101.md) |
| S-201 | Typical Slab Details | Structural | A | 2026-01-15 | [S-201.md](drawings/S-201.md) |
| ... | ... | ... | ... | ... | ... |

---

## Architectural

- **A-001 — Cover Sheet & Drawing Register** (Rev C, 2026-03-12). [A-001.md](drawings/A-001.md). Cover sheet listing all architectural drawings + general notes.
- **A-101 — Ground Floor Plan** (Rev B, 2026-02-04). [A-101.md](drawings/A-101.md). Full ground-floor plan, grid A–G / 1–8, with structural overlay and door swings.
- ...

## Structural

- ...

## [Other disciplines as present]

- ...
```

### Per-sheet description — what to include

The per-sheet `.md` files should be **exhaustive**. The reader should be able to answer almost any non-quantity question about the sheet from the `.md` alone. Cover, where present:

- View type (plan / section / elevation / detail) and what is shown zone-by-zone
- Every system represented and its routes/locations
- Every material, grade, size, manufacturer, model named on the sheet
- Every schedule (full content for small schedules; structure + row count for large)
- Every annotation, general note, construction note, detail bubble
- All cross-references to other sheets and specs
- Trade-perspective implications even on off-trade sheets

### Per-sheet materials & specs — only what's called out ON the drawing

Don't infer. If the drawing doesn't name the material, don't invent one. Reference the specification if the drawing points to it.

### What to skip

- Quantity counts (use `construction-takeoff` instead)
- Exact full setout dimension takeoffs
- Retyping specification clause wording in full
```
