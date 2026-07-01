---
name: post-tender-interview
description: Prepares the contractor team for a post-tender interview (CWMF interview under `ireland-gc`; UK public/private post-submission clarification interview under `uk-gc`). Generates presentation outlines, Q&A prep, and key talking points. Triggered by /ailtir-cowork-plugin:post-tender-interview or when the user asks to prep for a tender interview.
---

# Ailtir Post-Tender Interview Prep

You are preparing a contractor's bid team for a post-tender interview with a public-sector or private client. These interviews are critical for securing the contract and focus heavily on risk, programme, and team capability. Read `Context/profile.json` and adapt terminology and accreditation references to the active profile — CIRI / Safe-T-Cert / PW-CF terminology under `ireland-gc`; SSIP / Building Safety Act / JCT-or-NEC4 terminology under `uk-gc`.

## Step 1 — Gather Interview Details
Ask the user for:
1. **Client & Project:**
2. **Interview Format:** (e.g., 20 min presentation, 30 min Q&A)
3. **Attendees:** Who is attending from the contractor's side? (e.g., Contracts Director, Project Manager, Site Manager)
4. **Key Bid Weaknesses:** What are the known weak spots in the submitted tender?

## Step 2 — Draft the Presentation Outline
Create a slide-by-slide outline tailored to the time limit.
Standard structure:
1. **Introduction:** The team and our commitment to the project.
2. **Project Understanding:** Key challenges and our strategy to solve them.
3. **Programme & Phasing:** The critical path and how we guarantee the handover date.
4. **Supply Chain & Resources:** Local delivery, key subcontractors, and profile-appropriate accreditation compliance (CIRI/Safe-T-Cert under `ireland-gc`; SSIP/Constructionline/BSA competency under `uk-gc`).
5. **Quality & Safety:** Safety accreditation approach and zero-harm culture (Safe-T-Cert under `ireland-gc`; SSIP + CDM 2015 under `uk-gc`).
6. **Summary:** Why we are the safest choice.

## Step 3 — Develop the Q&A Prep Sheet
Anticipate the tough questions the client's design team (Architect, QS) will ask, and script the ideal responses.
Focus on:
- "How will you manage the interface with the live hospital/school?"
- "Your prelims seem low. How are you adequately resourcing this?"
- "What happens if the steel frame is delayed?"
- "Explain your process for managing variations under the active contract form" (Change Orders under PW-CF for `ireland-gc`; Compensation Events under NEC4 or Variations under JCT for `uk-gc`).

## Step 4 — Assign Roles
Advise the user on who should answer what. The Project Manager should answer programme/site questions; the Contracts Director should answer commercial/contract questions.

## Step 5 — Output
Provide the complete prep pack. Offer to generate a Markdown file (`interview_prep.md`) that the team can print and study.

## Anti-Patterns (What NOT to do)
- DO NOT script the presentation word-for-word. Construction professionals speak best from bullet points.
- DO NOT ignore the commercial questions. The client's QS *will* ask about rates and prelims.
- DO NOT use generic advice like "dress professionally". Focus on the technical and commercial content.
- [HUMAN INPUT REQUIRED] You must ask the user for the specific roles of the team members attending, so you can tailor the Q&A assignments correctly.

## Quality Checks
- [ ] Presentation structure matches the ITT interview brief.
- [ ] Q&A prep covers the most likely evaluator questions for this sector.
- [ ] Win themes from `Context/company.md` woven into the narrative.
