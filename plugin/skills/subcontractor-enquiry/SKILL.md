---
name: subcontractor-enquiry
description: Prepares subcontractor enquiry packs based on the package breakdown. Triggered by /ailtir-cowork-plugin:subcontractor-enquiry.
---

# Ailtir Subcontractor Enquiry Prep

You are preparing the formal enquiry packages to send to subcontractors.

## Step 1 — Gather Details
Ask the user:
- Which trade package are we sending out?
- What is the return date for the quotes?

## Step 2 — Draft the ITT Letter
Draft the Invitation to Tender (ITT) letter for the subcontractor.
Include:
- Project overview.
- Scope of works (reference the specific spec sections and drawings from the Package Register).
- Return date and instructions.
- Head Contract flow-downs (e.g., retention, DLP, insurances required).

## Step 3 — Compile the Pack
Instruct the user to create a ZIP file containing:
- The drafted ITT Letter.
- The relevant drawings and specs.
- The Pricing Schedule (if a BOQ is provided).

## Step 4 — Present
Provide the drafted ITT letter.

- [HUMAN INPUT REQUIRED] Confirm the return date and scope with the user before drafting the ITT letter.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate the return date. Ask the user.
- DO NOT guess the scope. Reference the specific spec sections and drawings from the Package Register.
- DO NOT forget to include the Head Contract flow-downs.

## Quality Checks
- [ ] ITT letter references the correct spec sections and drawing series.
- [ ] Head contract flow-downs (retention, DLP, insurances) included.
- [ ] Return date and instructions clearly stated.
