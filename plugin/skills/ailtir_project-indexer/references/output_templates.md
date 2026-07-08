# Output Templates — `ailtir_project-indexer`

Reference loaded by `SKILL.md` for Steps 3–6: writing `CLAUDE.md`,
`project.md`, per-sheet drawing `.md` files, and combined `drawings.md`.
Every skeleton is Ailtir-specific — the nine-section bid folder layout
from `create_bid_folders.py`, profile-aware currency and contract
references from `Context/profile.json`, and ISO 19650 status/revision
codes on every drawing artefact.

## How to use these templates

- Templates are not rigid forms — adapt sections to what the pack
  contains. Sections marked `_[optional]_` may be dropped.
- Markdown only. No emojis, no HTML. ATX headings, GitHub tables.
- First line of every generated file:
  `_Generated {YYYY-MM-DD} by ailtir_project-indexer. Re-run the skill to refresh._`
- **Currency:** read `Context/profile.json` and render `€` for
  `ireland-gc`, `£` for `uk-gc`. Never hardcode.
- **Contract-form references:**
  - `ireland-gc`: PW-CF1–5, RIAI Yellow/Blue/White, ARM4, SCSI, CWMF.
  - `uk-gc`: JCT 2024 (SBC/DB/IC/MW), NEC4 Options A–F, NRM1/NRM2, BCIS.
  - Never emit AS 4000 (Australia) or ConsensusDocs (US).
- **Status / revision codes** — see `research/drawing-conventions.md`
  for ISO 19650 S/A/B and P01/C01 tables. Cite the code; do not restate.
- **Cross-skill hand-offs:** quantities to `ailtir_takeoff`, open
  queries to `ailtir_rfi-generator`, evaluation criteria to
  `ailtir_compliance-matrix`, rates to `ailtir_rate-library`, packages
  to `ailtir_subcontractor-enquiry`.

---

## Template 1 — `CLAUDE.md` (entry point, under 300 lines)

Loaded into every downstream session under the bid. Keep it dense;
push detail into `project.md`.

```markdown
# {BidRef} — {ProjectName} — Claude Context Guide

_Generated {YYYY-MM-DD} by ailtir_project-indexer. Re-run the skill to refresh._

## About this bid

{2–4 sentences: client, procurement route from profile, project type,
approximate value, location, headline scope.}

## Bid state at a glance

| Field                | Value                                        |
|----------------------|----------------------------------------------|
| Phase                | {from Bids/{BidRef}/README.md frontmatter}   |
| Next action          | {from README frontmatter}                    |
| Blockers             | {from README frontmatter}                    |
| Tender return        | {date + time from ITT}                       |
| Site visit           | {date or "not scheduled"}                    |
| Clarifications close | {date}                                       |

## Folder structure

```
Bids/{BidRef}/
├── 00_Bid_Management/   bid/no-bid, decision log, hand-off notes
├── 01_Tender_Docs/      ITT, contract, drawings, specifications
├── 02_Analysis/         compliance matrix, risk register, go/no-go
├── 03_Estimate/         priced BoQ, rates, cost plan, backup
├── 04_Enquiries/        sub-contractor RFQs, returns, comparisons
├── 05_Submissions/      draft + final submission documents
├── 06_Programme/        MSP/Asta files, milestone tracker
├── 07_Correspondence/   RFIs sent/received, clarifications
├── 08_Post-Award/       (populated after award)
└── 0. AI Context/       indexer outputs
```

## Where to find what

| Question                        | Location                                   |
|---------------------------------|--------------------------------------------|
| Contract terms and amendments   | `01_Tender_Docs/Contract/`                 |
| ITT and evaluation criteria     | `01_Tender_Docs/ITT/`                      |
| Drawings (originals / per-sheet)| `01_Tender_Docs/Drawings/`, `0. AI Context/drawings_split/` |
| Compliance matrix               | `02_Analysis/Compliance_Matrix.xlsx`       |
| Rates and benchmarks            | `03_Estimate/Rates/`                       |
| Trade enquiries and returns     | `04_Enquiries/`                            |
| Draft and final submissions     | `05_Submissions/`                          |
| Programme and Gantt output      | `06_Programme/`                            |
| Sent/received RFIs              | `07_Correspondence/RFIs/`                  |

## Related context files (in `0. AI Context/`)

- `project.md` — narrative summary; contract clauses, scope, commercial position.
- `drawings.md` — drawing register with per-discipline sub-sections.
- `drawings_split/*.pdf` — one PDF per sheet.
- `{sheet_id}.md` — one file per sheet, keyed by ISO 19650 drawing
  number where available, else `<stem>_sheet<N>`.

## Analysis perspective

{From Step 5a — "General Contractor (all-trade coverage)" for a
main-contract bid, or a trade lens: Electrical / Hydraulic /
Mechanical / Structural / Fire.}

## Active profile

- **Profile:** `{profile_id}` from `Context/profile.json`
- **Currency:** `{€ | £}`
- **Standards in scope:**
  - `ireland-gc`: PW-CF suite, RIAI forms, ARM4, SCSI cost data, CWMF.
  - `uk-gc`: JCT 2024, NEC4 (Options A–F), NRM1/NRM2, BCIS.

## Notes for Claude

- Generated `{YYYY-MM-DD}`. Re-run if the pack updates.
- **Quantities:** route measurement questions to `ailtir_takeoff`.
- **Open queries:** draft RFIs via `ailtir_rfi-generator`.
- **Commercial sensitivity:** rates and margin under `03_Estimate/`
  are confidential; do not surface in submission text.
```

### Worked example — `2026-014-CorkLibrary` under `ireland-gc`

```markdown
# 2026-014-CorkLibrary — New Central Library, Cork — Claude Context Guide

_Generated 2026-07-08 by ailtir_project-indexer. Re-run the skill to refresh._

## About this bid

Cork City Council are procuring a new 4,200 m² central library on
Grand Parade under the CWMF Restricted route, using PW-CF1. Two-stage
tender; this pack is the Stage 2 fully-priced return. Value stated
€18.4m excl. VAT.

## Bid state at a glance

| Field                | Value                                           |
|----------------------|-------------------------------------------------|
| Phase                | pricing (Stage 2)                               |
| Next action          | close Package 4 (M&E) enquiries                 |
| Blockers             | RFI-011 fire-strategy zones outstanding         |
| Tender return        | 2026-08-15 12:00 IST                            |
| Site visit           | 2026-07-22 10:00                                |
| Clarifications close | 2026-07-31 17:00                                |

## Analysis perspective

General Contractor (all-trade coverage).

## Active profile

- **Profile:** `ireland-gc`  •  **Currency:** `€`
- **Standards in scope:** PW-CF1, ARM4, RIAI Working Drawings,
  SCSI Q3 2026 tender-price data; BCAR Assigned Certifier required.

## Notes for Claude

- Fire-compartment query — route to `ailtir_takeoff` (FIRE-A-101 C01).
- RFI-011 open at `07_Correspondence/RFIs/RFI-011.md`.
- Tender target €17.9m — do not restate outward.
```

---

## Template 2 — `project.md` (narrative summary)

The deep record; may grow to 2,000+ lines on large packs — it exists
precisely to replace re-reading 50+ PDFs on every downstream question.

```markdown
# {BidRef} — {ProjectName} — Project Summary

_Generated {YYYY-MM-DD} by ailtir_project-indexer. Re-run the skill to refresh._

## 1. Project overview

- Project name, `{BidRef}`, client/employer + client rep
- Procurement route ({`ireland-gc`: CWMF Restricted / Open / Private Negotiated / D&B / Framework;
    `uk-gc`: Open / Competitive Flexible / Direct Award / Framework Call-Off / Dynamic Market / Private Traditional or D&B})
- Principal consultants: architect, C&S, MEP, QS, PSDP / Principal Designer, fire, acoustic, sustainability
- Project type, address (with ITM/OSGB coordinates), approximate value `{€|£}{amount}`
- Contracting model ({`ireland-gc`: PW-CF1–5, RIAI Yellow/Blue/White, private D&B;
    `uk-gc`: JCT SBC/DB/IC/MW 2024, NEC4 Option A–F, private D&B})

## 2. Contract

- Form of contract and edition; contract date / tender return date
- Contract sum / tendered price `{€|£}{amount}`
- Amendments to the standard form (every deviation with clause ref)
- Notable risk allocations (ground, existing services, weather, contamination, TUPE, novation)
- Security / retention, LDs `{€|£}{amount}` per {day|week} capped at `{%}`, DLP / rectification period
- **Time-bar provisions:**
  - `ireland-gc` — PW-CF Contractor's Claim Notice within 20 working days
  - `uk-gc` NEC4 — Compensation Event notice within 8 weeks (Cl 61.3); JCT — Relevant Event notice "forthwith"
- Payment terms: interim cycle, pay-less notice deadlines

## 3. Scope

Inclusions, exclusions, spec highlights. Every substantive statement
cites source: `per Specification Section {N} §{clause}` or
`per Drawing {SheetID} Rev {code}`. Sub-section by trade or BoQ section.

## 4. Programme & key dates

| Milestone                        | Date         | Source            |
|----------------------------------|--------------|-------------------|
| Site visit                       | {YYYY-MM-DD} | ITT §{n}          |
| Clarifications close             | {YYYY-MM-DD} | ITT §{n}          |
| Tender return                    | {YYYY-MM-DD} | ITT §{n}          |
| Interview / clarification        | {YYYY-MM-DD} | ITT §{n}          |
| Expected start on site           | {YYYY-MM-DD} | ITT §{n}          |
| Sectional / practical completion | {YYYY-MM-DD} | Contract Appendix |

## 5. Commercial position

**Live bid:** tender price, target margin _[internal]_, PS/PC sums,
dayworks allowance, contingency.
**Post-award (when `08_Post-Award/` populated):** contract sum,
approved / pending variations, claims, retention, next valuation.

## 6. Open items

Outstanding RFIs, pending variations, overdue submittals. Draft new
RFIs via `ailtir_rfi-generator`.

## 7. Site conditions & constraints

Access, working hours, environmental targets (BREEAM UK; Home
Performance Index / NZEB IE; LEED; Passivhaus), heritage / archaeology
(RPS IE; listed UK), utilities capacity, neighbour constraints,
Section 106 (uk-gc) or Part V social housing (ireland-gc), site
hazards from the pre-construction information.

## 8. Compliance requirements

Profile-specific — populate whichever block matches
`Context/profile.json`. Cross-check via `ailtir_compliance-matrix`.

**If `ireland-gc`:**

- CIRI membership number
- Safe-T-Cert accreditation and expiry
- BCAR — Assigned Certifier appointment; Design Certifier if design
  responsibility rests with the contractor
- PSDP / PSCS appointments and competence evidence (SI 291/2013)
- Revenue Tax Clearance Certificate (eTC)
- PW-CF Suitability Assessment thresholds — turnover, personnel,
  insurance, similar projects
- CWMF form-of-tender declarations

**If `uk-gc`:**

- SSIP membership — CHAS, SafeContractor, or Constructionline (Gold)
- CDM 2015 Principal Contractor / Principal Designer appointments
- Building Safety Act 2022 — HRB Gateway 2 / 3 obligations if
  Higher-Risk Building
- Modern Slavery Act 2015 §54 statement (if turnover threshold met)
- Carbon Reduction Plan aligned to PPN 06/20 (central-government)
- Social Value response aligned to PPN 06/21 (central-government)
- Fire Safety (England) Regulations 2022 (residential)

## 9. Other material information

Long-lead items with lead time and impact, novated packages, disputes
on adjacent contracts, unusual specifications, single-source suppliers.

## 10. Source documents

| Filename            | Folder                     | Role                      | Read date    |
|---------------------|----------------------------|---------------------------|--------------|
| {tender-doc.pdf}    | `01_Tender_Docs/ITT/`      | Instructions to Tenderers | {YYYY-MM-DD} |
| {contract.pdf}      | `01_Tender_Docs/Contract/` | Form of Contract          | {YYYY-MM-DD} |
| {specification.pdf} | `01_Tender_Docs/Spec/`     | Specification             | {YYYY-MM-DD} |

## 11. Gaps

Information a downstream session might expect but that is absent from
the folder. Flag each so `ailtir_rfi-generator` can pick it up.
```

---

## Template 3 — Per-sheet drawing `.md`

Filename `<sheet_id>.md` where `sheet_id` is
`title_block.hints.sheet_number` from `process_drawing.py` (e.g.
`A-101.md`, `E-201.md`, or full ISO 19650 form
`OFF-HEX-ZZ-01-DR-A-0001.md`). Fall back to `<source_stem>_sheet<N>.md`.

```markdown
# {SheetID} — {SheetTitle}

_Generated {YYYY-MM-DD} by ailtir_project-indexer. Re-run the skill to refresh._

## Header

| Field                | Value                                                   |
|----------------------|---------------------------------------------------------|
| Sheet ID             | `{sheet_id}`                                            |
| Title                | {as printed}                                            |
| Discipline           | {mapped from role code — see `research/drawing-conventions.md`} |
| Revision             | `{P01 / P02 / C01 / C02 …}` (drawing-conventions.md)    |
| Status / Suitability | `{S0 / S1 / S2 / S3 / S4 / A1 / B1}` (drawing-conventions.md) |
| Revision date        | `{YYYY-MM-DD}`                                          |
| Scale(s)             | `1:{n} @ A{n}`                                          |
| Drawn / Checked / Approved | {initials}                                        |

## Source PDF

- Single-sheet: `0. AI Context/drawings_split/{filename}.pdf`
- Multi-sheet issue file: `01_Tender_Docs/Drawings/{filename}.pdf`

## Analysis perspective

{From Step 5a. Every content section below is written through this lens.}

## Quantities notice

This file describes what the sheet shows; it does not carry quantities.
Invoke `ailtir_takeoff` for measurement, area, count, or length —
that skill reads the split PDF, applies NRM2 rules of measurement,
and writes results into the estimate template.

## View and content

Exhaustive prose, zone by zone.

- **Plans** — walk rooms / zones / grid intersections.
- **Sections / elevations** — walk levels top-to-bottom, name each
  storey, describe construction, foreground vs background.
- **Details** — assembly name, scale, parent sheet reference,
  layer-by-layer build-up.

## Systems and elements present

Every system shown: structural, drainage, mechanical (heating /
cooling / ventilation), electrical (power / lighting / small power),
comms / data, fire (detection / suppression / compartmentation),
lifts, controls.

## Materials and specifications called out

Only what is named ON the sheet. Reference the parent spec section:
`per Spec §{n}`. Do not import from other sheets.

## Schedules on the sheet

- Under ~20 rows: reproduce fully as a markdown table.
- Larger: summarise (column names, row count, representatives) and
  cite sheet + spec for full data.

## Annotations, notes, callouts

- General notes and construction notes: verbatim (load-bearing).
- Detail bubbles: each with cross-reference.
- Key dimensional callouts: FFL, RL, setout, benchmarks.
- Hold points and inspection points.

## Cross-references

Other sheets referenced (with revision), spec sections, RFIs, revision
clouds, addendum items.

## {Perspective}-relevant implications

Trade-perspective lens — surface implications even on off-trade sheets.

- **Electrical:** containment crossing fire compartment lines,
  ceiling-void depth constraints, riser routing from elevations.
- **Mechanical:** riser locations, plantroom clear headroom,
  penetration coordination, external plant zones.
- **Structural:** transfer conditions, load paths, temporary works,
  setout tolerances.
- **Hydraulic / public health:** drainage invert levels, riser
  positions, water storage locations.
- **GC (main contractor):** logistics, sequencing, trade interface
  risks, temporary works, access hoist positions.
- **Fire:** compartment lines, cavity barriers, smoke seals, escape
  distances, means-of-escape widths.

## Gaps and notes for downstream sessions

Missing legends, cable sizes deferred to Contractor Design Portion,
structural sizes tagged "TBC", spec references to sections not in the
pack. Flag each so `ailtir_rfi-generator` can pick them up.
```

---

## Template 4 — Combined `drawings.md` (register + index)

Target under 500 lines even on large packs — the register carries
one-line pointers; depth lives in per-sheet files.

```markdown
# {BidRef} — {ProjectName} — Drawings

_Generated {YYYY-MM-DD} by ailtir_project-indexer. {N} sheets indexed. Re-run the skill to refresh._

## Analysis perspective

{Same value as CLAUDE.md.}

## Notice

- Per-sheet detail lives in the `{sheet_id}.md` files alongside this file.
- Split PDFs for single-sheet reading are in `0. AI Context/drawings_split/`.
- Quantities are not derived here — invoke `ailtir_takeoff`.

## Drawing register

Sorted by discipline then sheet number. Status and revision codes per
ISO 19650 (see `research/drawing-conventions.md`).

| Sheet ID | Title                          | Discipline    | Rev | Status | Date       | File                |
|----------|--------------------------------|---------------|-----|--------|------------|---------------------|
| A-101    | Ground Floor GA Plan           | Architectural | C01 | A1     | 2026-06-14 | [A-101.md](A-101.md)|
| A-201    | North & East Elevations        | Architectural | C01 | A1     | 2026-06-14 | [A-201.md](A-201.md)|
| S-100    | General Notes & Foundations    | Structural    | C02 | A1     | 2026-06-28 | [S-100.md](S-100.md)|
| M-201    | Ground Floor Ventilation Layout| Mechanical    | P03 | S2     | 2026-06-30 | [M-201.md](M-201.md)|
| E-101    | Ground Floor Small Power       | Electrical    | P02 | S2     | 2026-06-30 | [E-101.md](E-101.md)|

## Architectural

- **[A-101](A-101.md)** — Ground Floor GA Plan (C01, A1). Module grid,
  primary circulation, FFL datum used by every other discipline.
- **[A-201](A-201.md)** — North & East Elevations (C01, A1). Rainscreen
  zones, glazing modules, plant-screen extent.

## Structural

- **[S-100](S-100.md)** — General Notes & Foundations (C02, A1).
  Bearing capacity, transfer condition at grid D-4, pile schedule.

## Mechanical

- **[M-201](M-201.md)** — Ground Floor Ventilation (P03, S2). AHU-01
  supply layout; preliminary, awaiting fire-strategy sign-off.

## Electrical

- **[E-101](E-101.md)** — Ground Floor Small Power (P02, S2).
  Sockets, dedicated circuits, containment; outstanding coordination
  with mechanical riser at grid E-5.

## {Other disciplines present}

_One H2 per discipline present on the register. Single-line entries —
depth lives in the per-sheet `.md`._
```
