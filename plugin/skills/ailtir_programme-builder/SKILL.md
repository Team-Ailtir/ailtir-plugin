---
name: ailtir_programme-builder
description: Generates a tender programme (Gantt schedule) and narrative. Adapts phrasing to the active Ailtir profile — CWMF requirements for Ireland, Procurement Act 2023 / JCT / NEC4 requirements for UK. Triggered by /ailtir-cowork-plugin:ailtir_programme-builder or when the user asks for a project schedule.
---

# Ailtir Programme Builder

You are creating a tender programme (schedule) and accompanying narrative. Under `ireland-gc` this satisfies CWMF requirements for Irish public works tenders. Under `uk-gc` this satisfies typical JCT / NEC4 tender programme requirements — for NEC4 the Contractor's programme becomes the Accepted Programme under clause 31/32 once approved, so make sure the WBS supports subsequent Compensation Event assessment.

## Step 1 — Gather Project Parameters
Ask the user for:
1. **Start Date:**
2. **Required Completion Date / Duration:**
3. **Key Milestones:** (e.g., watertight, sectional handovers)
4. **Main Scope Elements:** (e.g., earthworks, steel frame, fit-out)

## Step 2 — Develop the Work Breakdown Structure (WBS)
Create a logical construction sequence:
1. Pre-construction & Mobilisation
2. Substructure / Groundworks
3. Superstructure (Frame, Floors, Roof)
4. Envelope / Watertight
5. MEP First Fix
6. Internal Partitions & Plastering
7. MEP Second Fix
8. Finishes (Floors, Ceilings, Joinery)
9. Commissioning & Snagging
10. Handover

## Step 3 — Generate the Programme Data
Create a table with: Task Name, Predecessor, Duration (Days), Start Date, End Date.
Ensure the critical path is logical (e.g., you cannot start first fix until the roof is on).

## Step 4 — Write the Programme Narrative
Most tenders (CWMF under `ireland-gc`; JCT/NEC4 under `uk-gc`) require a written narrative explaining the programme. Draft a 1-page document covering:
- **Overall Strategy:** How the project will be phased.
- **Critical Path:** Identification of the driving activities.
- **Risk Mitigation:** Weather allowances, long-lead procurement (e.g., switchgear, AHUs).
- **Resourcing:** Peak labour periods.

## Step 5 — Output
Provide the WBS table and the narrative. Offer to write the WBS data to a CSV file (`tender_programme.csv`) so the user can import it into Asta Powerproject or MS Project.

## Anti-Patterns (What NOT to do)
- DO NOT create unrealistic overlapping tasks (e.g., painting while pouring concrete floors).
- DO NOT ignore the commissioning period — always allow 2-4 weeks at the end for testing and snagging.
- DO NOT use US date formats (MM/DD/YYYY). Both supported profiles use DD/MM/YYYY.
- [HUMAN INPUT REQUIRED] Do not assume standard durations for complex elements like deep basements or specialist facades; ask the user if they have specific durations in mind.

## Quality Checks
- [ ] Critical path is logical — no impossible overlaps.
- [ ] Commissioning period included (minimum 2-4 weeks).
- [ ] DD/MM/YYYY date format used throughout.
- [ ] Written programme narrative covers overall strategy, critical path, and risk mitigation.
