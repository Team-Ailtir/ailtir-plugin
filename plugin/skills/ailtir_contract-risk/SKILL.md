---
name: ailtir_contract-risk
description: Reviews the tendered contract clause-by-clause against the playbook for the active Ailtir profile (Irish PW-CF/RIAI or UK JCT/NEC4). Triggered by /ailtir_contract-risk or when bid-planner runs.
---

# Ailtir Contract Risk Reviewer

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_contract-risk`
- `plugin_version`: `2.16.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are a Commercial Manager reviewing a proposed contract.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root to determine `profile_key` (either `ireland-gc` or `uk-gc`). The playbook you load in Step 3 depends on this value. If `profile.json` is missing, stop and tell the user to run `/ailtir_setup`.

## Step 2 — Identify the Form
Identify if the contract is one of the standard forms for the active profile:

- **Ireland (`ireland-gc`):** CWMF Public Works (PW-CF1 to PW-CF5), RIAI 2025 (or earlier), or bespoke / private D&B. Flag JCT/NEC contracts as unusual for the Irish profile.
- **UK (`uk-gc`):** JCT 2024 (SBC/Q or DB), NEC4 ECC (Option A/C most common), FIDIC where used on infrastructure, or bespoke / private D&B.

## Step 3 — Review against Playbook
Read `references/{profile_key}/contract-playbook.md` from this skill's directory. Scan the contract (specifically the Schedule of Amendments, Contract Data Part 1/2, Z clauses, or Employer's Requirements) for deviations from the playbook's standard positions:
- Liquidated Damages / Delay Damages (are they a genuine pre-estimate of loss?)
- Retention (flag if outside the playbook's standard band)
- Rectification / Defects Liability Period (typically 12 months; flag if longer)
- Time Bars — critical for NEC4 (strict 8-week Compensation Event bar) and PW-CF (strict 20 working days)
- Fitness for purpose language layered onto D&B (voids most PI cover)

## Step 4 — Generate the Workbook
This is the deep-dive pass. Assemble your clause-by-clause analysis into a JSON
payload, **write it to `/tmp/risk_data.json`**, then run the bundled
`scripts/create_risk_register.py` with `python3` — the script owns all tab
structure and styling; you supply the rows:

`python3 scripts/create_risk_register.py --output "Contract_Risk_Register_[Bid].xlsx" --data /tmp/risk_data.json`

Payload shape:

```json
{
  "cover": {"Project": "X", "Contract Form": "PW-CF5 v2.7", "Playbook Base": "ireland-gc"},
  "tabs": {
    "risk_register": {"rows": [["CR-01","20-Working-Day Time Bar","Sub-clause 10.3","RED","Loss of EOT","Notice register","Commercial Manager"]]},
    "contract_data": {"rows": [["Part 1A","ER","Employer's Representative","Named","Standard"]]},
    "action_tracker": {"rows": [["A-01","CR-01","Establish CE notice register","Commercial","START DATE","OPEN",""]]}
  }
}
```

This writes its OWN workbook — never the bid-planner file. If a section does not
apply, pass `"rows": []` with a `"na_note"`.

- [HUMAN INPUT REQUIRED] If the contract form cannot be determined from the documents, ask the user before proceeding.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate the risk positions. Use the contract playbook.
- DO NOT provide legal advice. Frame the output as commercial risk analysis.
- DO NOT skip reading the contract amendments (e.g., Z clauses or Part 1/2 schedules).

## Quality Checks
- [ ] `Context/profile.json` read; correct `profile_key` playbook loaded.
- [ ] Correct contract form identified.
- [ ] Deviations from standard playbook positions flagged.
- [ ] Risks prioritised by commercial impact.

## On Completion — Update Bid State

When this skill finishes for a specific bid, update the bid's state file so `ailtir_conductor` and `ailtir_dashboard` reflect the progress. Run the sibling `ailtir_conductor` skill's `scripts/update_frontmatter.py` helper with `python3`:

This deep dive **upgrades** the bid-planner's `summarised` entry to a full
`proceed`. Use `--result proceed`.

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
  → /{next_skill} — {one-line rationale from the phase map}

Or run /ailtir_conductor for a full cross-bid view.
```

Special cases:
- If `blockers[]` is non-empty, use the blocker's resolution skill from the phase map's blocker-overrides table instead (e.g. `ailtir_rfi-generator` for `type: rfi`) and lead with "Blocked — resolve first:".
- If every skill in the current phase's sequence is now completed, name the first skill of the next phase and say "Phase complete — moving to {next_phase}:".
- If the bid has reached `closed` or `delivery` with no obvious next step, print "No canonical next step — run `/ailtir_conductor` to see the full pipeline." instead of a specific recommendation.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
