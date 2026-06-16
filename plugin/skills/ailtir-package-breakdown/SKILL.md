---
name: ailtir-package-breakdown
description: Phase 2 skill. Converts project documents (head contract, specs, drawings) into a subcontractor trade package register and scope matrix. Triggered by /ailtir-cowork-plugin:package-breakdown.
user-invocable: false
disable-model-invocation: true
---

# Ailtir — Procurement Packaging

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" ailtir-package-breakdown >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" ailtir-package-breakdown > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" ailtir-package-breakdown >nul 2>nul
```

You are preparing procurement packages for an Irish construction project. Your job is to break the full scope into logical trade packages ready for the market.

## Step 1 — Scope Analysis

Review the documents in the workspace (Drawings, Specs, BOQ).
Build a comprehensive list of all required trades (e.g., Groundworks, Concrete Frame, Structural Steel, Roofing, Facades, M&E, Partitions, Ceilings, Finishes).

Extract Head Contract Flow-Downs: Find obligations in the main contract (PW-CF or RIAI) that must be passed down to subbies (e.g., 12-month DLP, 5% retention, specific insurances).

## Step 2 — Build the Package Register
List each package. For each, define:
- Scope inclusions
- Key interfaces (e.g., Groundworks interfaces with Concrete)
- Documents to include in the enquiry pack

Run the Python script to generate the Package Register Excel workbook:
```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/ailtir-package-breakdown/scripts/create_package_register.py" --output "Package_Register_[Project].xlsx"
```

- [HUMAN INPUT REQUIRED] Confirm the package list with the user before running the Python script.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate packages. Ensure every package traces back to the project scope.
- DO NOT miss the head contract flow-downs. They must be explicitly included in the package register.
- DO NOT run the Python script without replacing `[Project]` with the actual project name.

Populate the workbook with:
1. **Package List:** Every trade required, estimated value, and target procurement date.
2. **Scope Matrix:** Map specific spec sections and drawing series to each package. Flag interfaces (e.g., who supplies the cast-in plates for the steel? Concrete or Steel package?).

## Step 3 — Present

Provide the Excel workbook. Ask: "Would you like me to draft the Subcontractor Enquiry packs for any of these trades (`/ailtir-cowork-plugin:subcontractor-enquiry`)?"

## Quality Checks
- [ ] Every trade required for the project scope is represented as a package.
- [ ] Head contract flow-downs explicitly included in the package register.
- [ ] Interface risks between packages identified and flagged.
