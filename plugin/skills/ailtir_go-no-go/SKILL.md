---
name: ailtir_go-no-go
description: Evaluates bid viability against the accreditation gates and weighted scoring matrix appropriate to the active Ailtir profile (Irish CIRI/Safe-T-Cert or UK SSIP). Triggered by /ailtir-cowork-plugin:ailtir_go-no-go or when bid-planner runs.
---

# Ailtir Go/No-Go Evaluator

## Usage Reporting

Before doing workflow-specific work, call the `plugin_report_usage` tool from
the bundled `ailtir` MCP server with these arguments:

- `skill_name`: `ailtir_go-no-go`
- `plugin_version`: `2.15.0`

If reporting returns `failed`, leave the failure visible and continue the workflow.

You are evaluating a tender against the Go/No-Go framework for the active market.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root to determine `profile_key`. If it is missing, stop and tell the user to run `/ailtir-cowork-plugin:ailtir_setup`.

## Step 2 — Evaluate Mandatory Gates
Read the profile-appropriate criteria file from the sibling `bid-planner` skill's directory:

- `ireland-gc` → `references/ireland-gc/go-no-go-criteria.md` in the `bid-planner` skill.
- `uk-gc` → `references/uk-gc/go-no-go-criteria.md` in the `bid-planner` skill.

Check the user's `Context/company.md` against the tender requirements. The gates depend on profile:

- **Under `ireland-gc`:** Safe-T-Cert grade, CIRI registration, turnover ≥1.5×–2× annualised contract value, bond/insurance capacity, site management capacity.
- **Under `uk-gc`:** SSIP membership (CHAS / SafeContractor / Constructionline Gold / Achilles Building Confidence), ISO 9001/14001/45001, turnover ≥1.5×–2× annualised contract value, bond/insurance capacity, site management capacity, and — for Higher-Risk Buildings — BSA 2022 Principal Contractor competency, Modern Slavery s.54 statement (if company turnover ≥£36m), and a compliant Carbon Reduction Plan (for central government contracts >£5m/year).

If any gate fails, flag it as a **RED NO-GO RISK**.

## Step 3 — Score the Opportunity
Score the tender out of 100 using the four dimensions in the loaded criteria file:
1. Client & Relationship (30)
2. Sector & Experience (25)
3. Commercial & Contract (25) — note the scoring bands are profile-specific (PW-CF/RIAI risk allocation for `ireland-gc`; unamended JCT/NEC4 for `uk-gc`).
4. Competition & Procurement (20) — routes differ by profile (CWMF vs Procurement Act 2023 procedures).

## Step 4 — Present
Provide the final score and a recommendation (Strong GO, Marginal GO, NO-GO).
If called by the `bid-planner`, return the score to the orchestrator. If called directly, present it to the user.

- [HUMAN INPUT REQUIRED] If the tender pack is missing key data (e.g., contract value, procurement route), ask the user before scoring.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate the scoring weights. Read the loaded criteria file.
- DO NOT proceed if a mandatory gate is failed. Flag it immediately.
- DO NOT invent missing information; ask the user to clarify if the tender pack is missing data.
- DO NOT apply Irish accreditation gates to UK tenders (or vice versa).

## Quality Checks
- [ ] `Context/profile.json` read; correct `profile_key` criteria file loaded from the `bid-planner` skill's references.
- [ ] Mandatory gates for the active profile explicitly checked against actual context data.
- [ ] No hallucinated scores; every score justified by evidence from the tender pack.
- [ ] Final recommendation aligns with the scoring thresholds in the loaded criteria file.

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
