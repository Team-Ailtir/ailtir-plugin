---
name: ailtir:package-breakdown
description: Phase 2 skill. Converts project documents (head contract, specs, drawings) into a subcontractor trade package register and scope matrix. Triggered by /ailtir-cowork-plugin:package-breakdown.
---

# Ailtir — Procurement Packaging

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

Provide the Excel workbook. Ask: "Would you like me to draft the Subcontractor Enquiry packs for any of these trades (`/ailtir-cowork-plugin:subcontractor-enquiry`)?"

## Quality Checks
- [ ] Every trade required for the project scope is represented as a package.
- [ ] Head contract flow-downs explicitly included in the package register.
- [ ] Interface risks between packages identified and flagged.
