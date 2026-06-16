---
name: ailtir-site-diary
description: Transforms rough field notes or voice transcripts into a formal daily site diary compliant with PW-CF requirements. Triggered by /ailtir-cowork-plugin:site-diary or when the user drops field notes.
user-invocable: false
disable-model-invocation: true
---

# Ailtir Site Diary

You are transforming messy, unstructured field notes, WhatsApp messages, or voice transcripts from a Site Manager into a professional, formal daily site diary. This document is a critical commercial record under Irish Public Works Contracts (PW-CF).

## Step 1 — Ingest the Raw Notes
Read the provided text, transcript, or bullet points.

## Step 2 — Extract and Categorise
Organise the information into the following standard PW-CF site diary sections:
- **Date & Weather:** (Crucial for extension of time claims).
- **Labour on Site:** Direct staff and subcontractor headcounts.
- **Plant & Equipment:** Active and idle plant.
- **Work Executed Today:** Specific progress by area/trade.
- **Materials Delivered:** Key deliveries.
- **Delays / Issues:** Any impediments to progress (e.g., waiting on RFI response, design team changes).
- **Health & Safety:** Incidents, toolbox talks, inductions.
- **Verbal Instructions:** Any directions given by the Employer's Representative (ER).

## Step 3 — Draft the Formal Diary
Write the report using professional, objective language. Remove emotion, slang, and speculation.

*Example Translation:*
- *Raw:* "The architect finally showed up but didn't have the door schedules so we couldn't order them. Absolute joke."
- *Formal:* "Employer's Representative visited site. Door schedules remain outstanding; noted as a delay to procurement."

## Step 4 — Flag Commercial Triggers
If the notes contain evidence of a delay, a variation, or an instruction from the ER, explicitly flag this to the user at the bottom of the output. Advise them that a formal notice under the PW-CF may be required (referencing `ailtir-contract-admin`).

## Step 5 — Output
Provide the formatted diary. Offer to write it to a Markdown file (`Site_Diary_YYYY-MM-DD.md`) or generate a PDF using `manus-md-to-pdf`.

## Anti-Patterns (What NOT to do)
- DO NOT invent weather conditions, labour numbers, or progress if they are not in the notes. Mark them as `[Not Recorded]`.
- DO NOT use the term "Architect" or "Client" in the formal text if it's a PW-CF contract; use "Employer's Representative" (ER) and "Employer".
- DO NOT include emotional language, blame, or subjective opinions in the final diary. It must be factual.
- [HUMAN INPUT REQUIRED] If a critical delay is mentioned but the cause is unclear, ask the user to clarify before finalizing the diary.

## Quality Checks
- [ ] PW-CF terminology used: 'Employer's Representative' not 'Architect', 'Employer' not 'Client'.
- [ ] No emotional language, blame, or speculation in the formal diary.
- [ ] Commercial triggers (delays, variations, ER instructions) explicitly flagged.
- [ ] Missing data marked as `[Not Recorded]` — not invented.
