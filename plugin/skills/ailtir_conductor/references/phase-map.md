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

Tender pack in hand, decision to bid taken. The conductor's core sequence:

1. `ailtir_project-indexer` — catalogue every document, extract dates, flag missing files.
2. `ailtir_compliance-matrix` — extract every returnable and evaluation criterion from the ITT.
3. `ailtir_contract-risk` — clause-by-clause review against the profile-appropriate playbook.
4. `ailtir_pqq-manager` — if a PQQ / SQ / Supplier Info form is part of the pack.
5. `ailtir_package-breakdown` — trade package register + scope matrix.

**Advance criterion:** all five completed (or `pqq-manager` skipped because no PQQ is required). Bid advances to `estimating`.

**Alternatives / sideways moves at this phase:**

- `ailtir_rfi-generator` — draft an RFI whenever a gap is found (indexer flags a missing drawing, compliance matrix flags an unclear requirement).
- `ailtir_bid-planner` — the Phase-1 orchestrator that bundles indexer + go/no-go + compliance-matrix + contract-risk into one flow. Recommend as the alternative for users who prefer a single-command run.

---

## Phase: `estimating`

Packages defined. Pricing work begins.

1. `ailtir_takeoff` — quantities from drawings → NRM2 register.
2. `ailtir_subcontractor-enquiry` — draft ITT letters for each trade package.
3. `ailtir_prelims-builder` — priced schedule of prelims (ARM4/NRM1).
4. `ailtir_bid-leveling` — normalise sub quotes → like-for-like comparison, once quotes are back.
5. `ailtir_cost-reconciliation` — final estimate gap/benchmark check.

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

- `ailtir_intelligence-builder` — cross-phase. Do NOT put in the sequence. `ailtir_case-study-generator` (in `post-tender`) already prompts to feed it.
- `ailtir_dashboard`, `ailtir_prime`, `ailtir_setup`, `ailtir_notion-setup`, `ailtir_notion-second-brain`, `ailtir_enable-monitor`, `ailtir_opportunity-monitor`, `ailtir_feedback` — workspace-scoped, not bid-scoped. Never in a bid's `next_action`.
- `ailtir_rate-library` — support skill. Available inside estimating but not sequenced.
