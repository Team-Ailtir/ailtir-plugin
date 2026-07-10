---
name: ailtir_takeoff
description: Extracts elemental quantities from construction drawings (PDF) into an NRM2 elemental Excel register. NRM2 is common across `ireland-gc` and `uk-gc` profiles. Triggered by /ailtir-cowork-plugin:ailtir_takeoff or when the user asks to measure drawings.
allowed-tools:
  - mcp__plugin_ailtir-cowork-plugin_ailtir__plugin_report_usage
---

# Ailtir Takeoff

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_takeoff`
- `plugin_version`: `2.15.3`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are measuring construction quantities from tender drawings. This skill runs the Python takeoff scripts to extract counts, lengths, and areas, and formats them into an Excel register aligned with the RICS NRM2 elemental structure — the same structure is used under both `ireland-gc` (where SCSI adopts NRM2) and `uk-gc` (where NRM2 is the primary RICS standard for detailed measurement of building works).

## Step 1 — Verify the Request
Ask the user which drawing(s) they want measured and what elements they are looking for (e.g., "count all Type A doors on drawing A-101", "measure the blockwork walls on the ground floor plan").

## Step 2 — Run the Extraction Script
Run the bundled `scripts/extract.py` helper in this skill's directory on the specified drawing. The script uses PDF vector extraction and geometry reconstruction to find elements. Invoke it with `python3`, pass the drawing PDF path as the positional argument, and pass `-o takeoff.json` for output.

## Step 3 — Format to NRM2 Elemental Structure
The script outputs raw JSON. You must read the JSON and format it into a table that follows the NRM2 elemental structure (e.g., Substructure, Superstructure, Internal Finishes, Services).

For each item, list:
- **Element:** (e.g., Internal Walls)
- **Description:** (e.g., 100mm blockwork wall)
- **Quantity:**
- **Unit:** (m, m2, m3, nr)
- **Drawing Ref:**

## Step 4 — Run the Excel Output Script
Run the bundled `scripts/excel_output.py` helper in this skill's directory to generate the final Ailtir-branded workbook. Invoke it with `python3`, pass `takeoff.json` as the positional argument, and pass `-o takeoff_register.xlsx` for output. The workbook itself uses NRM2 headings for both profiles; downstream `estimating-workflow` handles the currency and rates.

Present the Excel file to the user.

## Anti-Patterns (What NOT to do)
- DO NOT attempt to measure drawings visually by just looking at the PDF image — always use the Python scripts.
- DO NOT use US Imperial units (feet/inches) or US CSI divisions. Both supported profiles use metric and the NRM2 elemental structure.
- DO NOT guarantee 100% accuracy. Always state the confidence level returned by the script.
- [HUMAN INPUT REQUIRED] If the drawing scale is not explicitly stated or detected by the script, you must ask the user to confirm the scale before proceeding.

## Quality Checks
- [ ] NRM2 elemental structure used for all quantity items.
- [ ] Quantities extracted from vector data, not estimated visually.
- [ ] Drawing reference included for every quantity item.
- [ ] User confirmed the takeoff before it is used for pricing.

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
