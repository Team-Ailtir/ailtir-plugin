# Phase Map — Canonical Skill Sequence Per Phase

This file drives the conductor's "next skill" recommendation. Each phase lists the expected sequence of skills; the conductor picks the earliest one not present in `completed[]`.

Phases are ordered. When every expected skill for a phase is completed, the bid advances to the next phase (the conductor rewrites `phase:` in the frontmatter).

---

## Phase: `opportunity`

The lead has been logged but a formal bid folder may not yet exist. The conductor rarely surfaces bids in this phase — most opportunities live in the Notion Bid Pipeline, not as folders. When a folder is created before go/no-go, the flow is:

1. `ailtir_go-no-go` — score the opportunity against profile gates.

**Advance criterion:** `ailtir_go-no-go` completed with `result: proceed`. Bid advances to `pre-bid`. If `result: no-bid`, set `status: no-bid` and stop.

---

## Phase: `pre-bid`

Tender pack in hand, decision to bid taken. The canonical entry point is the
Tier-1 planner, which produces a summarised first pass; the deep dives follow.

1. `ailtir_bid-planner` — the Tier-1 first pass. Produces one 9-tab workbook +
   kick-off deck. Does Go/No-Go **in full** (recorded `result: proceed`),
   **summarises** compliance and contract-risk (recorded `result: summarised`),
   and outlines packages for awareness (fully defined in the `estimating` phase).
2. `ailtir_contract-risk` — deep dive: full clause-by-clause register, contract
   data, action tracker. Upgrades the `summarised` entry to `proceed`.
3. `ailtir_compliance-matrix` — deep dive: full returnables tracker with
   templates, owners, deadlines. Upgrades the `summarised` entry to `proceed`.
4. `ailtir_pqq-manager` — if a PQQ / SQ / Supplier Info form is part of the pack.

**`summarised` handling:** a skill whose latest `completed[]` entry has
`result: summarised` is NOT done — surface it as the next step, but frame it as a
deep dive, e.g. *"Summarised in the bid plan — run for the full clause-by-clause
review."* Never present it as a blind repeat. Once its entry is `proceed` (or
`skipped`), treat it as complete.

**Advance criterion:** `bid-planner` done, `contract-risk` and
`compliance-matrix` both at `result: proceed` (or `skipped`), and `pqq-manager`
done or skipped (no PQQ). Bid advances to `estimating`.

**Alternatives / sideways moves at this phase:**

- `ailtir_rfi-generator` — draft an RFI whenever a gap is found.

---

## Phase: `estimating`

Packages defined. Pricing work begins.

1. `ailtir_package-breakdown` — define trade packages; every downstream estimating step depends on them.
2. `ailtir_takeoff` — quantities from drawings → NRM2 register.
3. `ailtir_subcontractor-enquiry` — draft ITT letters for each trade package.
4. `ailtir_prelims-builder` — priced schedule of prelims (ARM4/NRM1).
5. `ailtir_bid-leveling` — normalise sub quotes → like-for-like comparison, once quotes are back.
6. `ailtir_cost-reconciliation` — final estimate gap/benchmark check.

**Advance criterion:** `ailtir_cost-reconciliation` completed. Bid advances to `submission`.

**Alternatives:**

- `ailtir_estimating-workflow` — the Phase-4 orchestrator that chains takeoff → prelims → rate-library → bid-leveling → cost-reconciliation.
- `ailtir_rate-library` — always available as a rate lookup; do not put this in the sequence, it is a support skill.
- `ailtir_rfi-generator` — for any pricing gap the estimator can't close without client clarification.

---

## Phase: `submission`

Numbers locked. Package the submission.

1. `ailtir_quality-writer` — draft technical / social value / method statement responses.
2. `ailtir_programme-builder` — tender programme + narrative.
3. `ailtir_bid-assembly` — compile the master submission document.
4. `ailtir_submission-preflight` — deterministic compliance check before send.

**Advance criterion:** `ailtir_submission-preflight` completed with pass result. Bid advances to `post-tender`. Update `status:` to `submitted` (add this to the frontmatter if not present).

---

## Phase: `post-tender`

Submission out. Waiting for feedback.

1. `ailtir_post-tender-interview` — only if the client invites the team to an interview.
2. On outcome (`status: won` or `status: lost`): `ailtir_case-study-generator` — capture debrief and, if won, seed a case study for the Intelligence folder.
3. `ailtir_feedback` — 1-10 rating on the bid experience.

**Advance criterion:** case-study-generator completed. If `status: won`, bid advances to `delivery`. If `status: lost`, advance to `closed`.

---

## Phase: `delivery`

Won bid, moved into build phase. The plugin's delivery skills are lighter than the bid-side ones.

1. `ailtir_site-diary` — recurring, run daily or as-needed.
2. `ailtir_contract-admin` — triggered whenever site-diary flags a delay, early-warning, CE, or L&E event.

**No advance criterion.** Delivery is open-ended. The user marks `status: closed` manually when the project completes.

---

## Phase: `closed`

Terminal. Conductor does not surface these bids in the top-3 ranking, but they remain queryable via "show all".

---

## Blocker Overrides

When a bid has a non-empty `blockers[]` list, the conductor overrides the phase-canonical next-skill with a resolution skill:

| Blocker type   | Resolution skill                      | Rationale                                    |
|----------------|---------------------------------------|----------------------------------------------|
| `rfi`          | `ailtir_rfi-generator`                | Draft / chase the RFI                        |
| `missing-doc`  | `ailtir_ingest`                       | Ingest the missing document once received    |
| `sub-quote`    | `ailtir_subcontractor-enquiry`        | Re-issue enquiry or chase the sub            |
| `client-decision` | (none — conductor surfaces and waits) | User escalates outside the plugin          |

If the blocker type is unknown, the conductor surfaces it but does not override — it just notes "Blocked; resolve before proceeding".

---

## Skill Availability Notes

- `ailtir_intelligence-builder` — cross-phase. Do NOT put in the sequence. Surface it as a soft conductor nudge at three moments:
  1. **Setup (seed):** conductor Step 7 in `ailtir_setup` recommends it explicitly so quality-writer has material from day one.
  2. **Post-tender (capture):** `ailtir_case-study-generator` already prompts to feed it after each bid closes.
  3. **Submission (thin Intelligence/):** if `Intelligence/` contains fewer than 2 files when a bid enters the `submission` phase, conductor adds a soft nudge — *"Intelligence/ looks thin — running `/ailtir_intelligence-builder` now will improve quality-writer drafts for this submission."* This is advisory only; it does NOT block or sequence the submission skills.
- `ailtir_dashboard`, `ailtir_prime`, `ailtir_setup`, `ailtir_notion-setup`, `ailtir_notion-second-brain`, `ailtir_enable-monitor`, `ailtir_opportunity-monitor`, `ailtir_feedback` — workspace-scoped, not bid-scoped. Never in a bid's `next_action`.
- `ailtir_rate-library` — support skill. Available inside estimating but not sequenced.
