---
name: ailtir_site-diary
description: Transforms rough field notes or voice transcripts into a formal daily site diary. Under `ireland-gc` the diary is compliant with PW-CF requirements; under `uk-gc` it captures the equivalent daily record required to support NEC4 Compensation Event assessment and JCT Extension of Time / Loss & Expense claims. Triggered by /ailtir-cowork-plugin:ailtir_site-diary or when the user drops field notes.
---

# Ailtir Site Diary

## Usage Reporting

Before doing workflow-specific work, call the `plugin_report_usage` tool from
the bundled `ailtir` MCP server with these arguments:

- `skill_name`: `ailtir_site-diary`
- `plugin_version`: `2.15.1`

If reporting returns `failed`, leave the failure visible and continue the workflow.

You are transforming messy, unstructured field notes, WhatsApp messages, or voice transcripts from a Site Manager into a professional, formal daily site diary. This document is a critical commercial record — under Irish Public Works Contracts (PW-CF) it is directly referenced; under UK JCT and NEC4 forms the contemporaneous site record is central to Compensation Event assessment (NEC4 clause 63) and Loss & Expense ascertainment (JCT clause 4.20).

Read `Context/profile.json` before drafting so the terminology in Step 3 matches the contract form in use.

## Step 1 — Ingest the Raw Notes
Read the provided text, transcript, or bullet points.

## Step 2 — Extract and Categorise
Organise the information into the following standard site diary sections:
- **Date & Weather:** (Crucial for extension of time claims — Relevant Event 2.29.9 under JCT SBC / 2.26.8 under JCT DB / clause 60.1(13) under NEC4).
- **Labour on Site:** Direct staff and subcontractor headcounts.
- **Plant & Equipment:** Active and idle plant.
- **Work Executed Today:** Specific progress by area/trade.
- **Materials Delivered:** Key deliveries.
- **Delays / Issues:** Any impediments to progress (e.g., waiting on RFI response, design team changes).
- **Health & Safety:** Incidents, toolbox talks, inductions. Under `uk-gc` also note any CDM 2015 Principal Designer / Principal Contractor interactions and — on HRB projects — any Building Safety Act "golden thread" information events.
- **Verbal Instructions:** Any directions given by the Employer's Representative under `ireland-gc` PW-CF; by the Contract Administrator / Employer's Agent under JCT; by the Project Manager or Supervisor under NEC4.

## Step 3 — Draft the Formal Diary
Write the report using professional, objective language. Remove emotion, slang, and speculation.

*Example Translation:*
- *Raw:* "The architect finally showed up but didn't have the door schedules so we couldn't order them. Absolute joke."
- *Formal:* "Employer's Representative visited site. Door schedules remain outstanding; noted as a delay to procurement."

## Step 4 — Flag Commercial Triggers
If the notes contain evidence of a delay, a variation, or an instruction from the ER / CA / Project Manager, explicitly flag this to the user at the bottom of the output. Advise them that a formal notice may be required under the active contract form (referencing `contract-admin`) — PW-CF Delay/Cost Notice under `ireland-gc`; NEC4 Early Warning or Compensation Event notification / JCT Delay Notice under `uk-gc`.

## Step 5 — Output
Provide the formatted diary. Offer to write it to a Markdown file (`Site_Diary_YYYY-MM-DD.md`) or generate a PDF using `manus-md-to-pdf`.

## Anti-Patterns (What NOT to do)
- DO NOT invent weather conditions, labour numbers, or progress if they are not in the notes. Mark them as `[Not Recorded]`.
- DO NOT use casual terminology. Match the terminology of the active contract form: PW-CF → "Employer's Representative" (ER) and "Employer"; JCT SBC → "Contract Administrator" (CA) and "Employer"; JCT DB → "Employer's Agent" and "Employer"; NEC4 → "Project Manager" / "Supervisor" and "Client".
- DO NOT include emotional language, blame, or subjective opinions in the final diary. It must be factual.
- [HUMAN INPUT REQUIRED] If a critical delay is mentioned but the cause is unclear, ask the user to clarify before finalizing the diary.

## Quality Checks
- [ ] Terminology matches the active contract form (ER/Employer under PW-CF; CA or Employer's Agent under JCT; Project Manager / Supervisor / Client under NEC4).
- [ ] No emotional language, blame, or speculation in the formal diary.
- [ ] Commercial triggers (delays, variations, formal instructions) explicitly flagged.
- [ ] Missing data marked as `[Not Recorded]` — not invented.
