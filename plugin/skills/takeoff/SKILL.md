---
name: takeoff
description: Extracts elemental quantities from construction drawings (PDF) into an Irish-standard (SCSI/NRM2) Excel register. Triggered by /ailtir-cowork-plugin:takeoff or when the user asks to measure drawings.
---

# Ailtir Takeoff

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" takeoff >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" takeoff > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" takeoff >nul 2>nul
```

You are measuring construction quantities from tender drawings. This skill runs the Python takeoff scripts to extract counts, lengths, and areas, and formats them into an Excel register aligned with Irish estimating practice.

## Step 1 — Verify the Request
Ask the user which drawing(s) they want measured and what elements they are looking for (e.g., "count all Type A doors on drawing A-101", "measure the blockwork walls on the ground floor plan").

## Step 2 — Run the Extraction Script
Run the `extract.py` script on the specified drawing. The script uses PDF vector extraction and geometry reconstruction to find elements.

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run_python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/takeoff/scripts/extract.py" [drawing.pdf] -o takeoff.json
```

## Step 3 — Format for Irish Practice
The script outputs raw JSON. You must read the JSON and format it into a table that follows the SCSI / NRM2 elemental structure (e.g., Substructure, Superstructure, Internal Finishes, Services).

For each item, list:
- **Element:** (e.g., Internal Walls)
- **Description:** (e.g., 100mm blockwork wall)
- **Quantity:**
- **Unit:** (m, m2, m3, nr)
- **Drawing Ref:**

## Step 4 — Run the Excel Output Script
Run the `excel_output.py` script to generate the final Ailtir-branded workbook.

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run_python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/takeoff/scripts/excel_output.py" takeoff.json -o takeoff_register.xlsx
```

Present the Excel file to the user.

## Anti-Patterns (What NOT to do)
- DO NOT attempt to measure drawings visually by just looking at the PDF image — always use the Python scripts.
- DO NOT use US Imperial units (feet/inches) or US CSI divisions. Ireland uses metric and SCSI/NRM2 elemental structures.
- DO NOT guarantee 100% accuracy. Always state the confidence level returned by the script.
- [HUMAN INPUT REQUIRED] If the drawing scale is not explicitly stated or detected by the script, you must ask the user to confirm the scale before proceeding.

## Quality Checks
- [ ] SCSI/NRM2 elemental structure used for all quantity items.
- [ ] Quantities extracted from vector data, not estimated visually.
- [ ] Drawing reference included for every quantity item.
- [ ] User confirmed the takeoff before it is used for pricing.
