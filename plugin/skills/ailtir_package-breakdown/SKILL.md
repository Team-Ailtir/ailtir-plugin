---
name: ailtir_package-breakdown
description: Phase 2 skill. Converts project documents (head contract, specs, drawings) into a subcontractor trade package register and scope matrix. Triggered by /ailtir_package-breakdown.
---

# Ailtir — Procurement Packaging

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_package-breakdown`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are preparing procurement packages for a construction project. Your job is to break the full scope into logical trade packages ready for the market. Read `Context/profile.json` to understand which contract form regime applies — this drives the flow-down obligations you extract in Step 1.

## Step 1 — Scope Analysis

Review the documents in the workspace (Drawings, Specs, BOQ).
Build a comprehensive list of all required trades (e.g., Groundworks, Concrete Frame, Structural Steel, Roofing, Facades, M&E, Partitions, Ceilings, Finishes).

Extract Head Contract Flow-Downs: find obligations in the main contract that must be passed down to subcontractors. Typical items to flow down:
- Under `ireland-gc` (PW-CF or RIAI): 12-month Defects Liability Period, 5% retention, PSDP/PSCS coordination, CAR insurance, specific bonding requirements.
- Under `uk-gc` (JCT or NEC4): Rectification Period, retention percentage per the head contract, Collateral Warranties / third-party rights, CDM 2015 duties, Building Safety Act information-transfer duties on HRB projects, and — where applicable — Named Suppliers under NEC4 Option X10 or Sub-Contractor approval procedure under JCT.

## Step 2 — Build the Package Register
List each package. For each, define:
- Scope inclusions
- Key interfaces (e.g., Groundworks interfaces with Concrete)
- Documents to include in the enquiry pack

Run the bundled `scripts/create_package_register.py` helper in this skill's directory to generate the Package Register Excel workbook. Invoke it with `python3` and pass:
- `--output "Package_Register_[Project].xlsx"`

- [HUMAN INPUT REQUIRED] Confirm the package list with the user before running the Python script.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate packages. Ensure every package traces back to the project scope.
- DO NOT miss the head contract flow-downs. They must be explicitly included in the package register.
- DO NOT run the Python script without replacing `[Project]` with the actual project name.

Populate the workbook with:
1. **Package List:** Every trade required, estimated value, and target procurement date.
2. **Scope Matrix:** Map specific spec sections and drawing series to each package. Flag interfaces (e.g., who supplies the cast-in plates for the steel? Concrete or Steel package?).

## Step 3 — Present

Provide the Excel workbook. Ask: "Would you like me to draft the Subcontractor Enquiry packs for any of these trades (`/ailtir_subcontractor-enquiry`)?"

## Quality Checks
- [ ] Every trade required for the project scope is represented as a package.
- [ ] Head contract flow-downs explicitly included in the package register.
- [ ] Interface risks between packages identified and flagged.

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
