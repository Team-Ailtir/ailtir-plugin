---
name: takeoff
description: Extracts elemental quantities from construction drawings (PDF) into an NRM2 elemental Excel register. NRM2 is common across `ireland-gc` and `uk-gc` profiles. Triggered by /ailtir-cowork-plugin:takeoff or when the user asks to measure drawings.
---

# Ailtir Takeoff

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
