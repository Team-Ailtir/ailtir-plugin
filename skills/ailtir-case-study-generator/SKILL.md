---
name: ailtir-case-study-generator
description: Converts completed project data into structured case studies, and processes tender debriefs to extract learning signals. Triggered by /ailtir-cowork-plugin:case-study-generator or debrief mode.
user-invocable: false
disable-model-invocation: true
---

# Ailtir Case Study Generator & Debrief Processor

You have two modes: generating case studies for completed projects, and processing tender debriefs to extract learning signals.

---

## MODE 1: Case Study Generation
*Use this mode when the user wants to write up a completed project.*

### Step 1 — Gather Data
Ask the user for:
- Project Name & Location
- Client & Architect
- Final Value
- Dates (Start and Completion)
- A brief description of the works
- Key challenges overcome

## Step 2 — Draft the Case Study
Structure the case study using the STAR method (Situation, Task, Action, Result):
- **Project Overview (Situation):** The basic facts and figures.
- **Scope of Works (Task):** What was built.
- **Challenges & Solutions (Action):** How the team solved problems (this is the most important part for winning future work).
- **Outcomes (Result):** Any relevant metrics (e.g., zero accidents, BREEAM Excellent, delivered on time/budget).
Ensure it highlights the company's win themes (read `Context/company.md`).

### Step 3 — Present
Provide the drafted case study. Instruct the user to save it to their `Resources/` folder.

---

## MODE 2: Tender Debrief Processing
*Use this mode when the user uploads a tender outcome letter or debrief matrix.*

### Step 1 — Extract the Data
Extract the following from the debrief document:
- The winning contractor (if disclosed)
- Our total score vs the winning score
- Our price vs the winning price
- The score differential on every individual quality criterion

### Step 2 — Language Pattern Analysis
Map the evaluator's commentary to actionable lessons for the Quality Writer.
- If they said "Lacked specific detail" → Note: "We need more quantified, site-specific content."
- If they said "Did not fully address" → Note: "We missed a sub-criterion; check compliance matrix coverage."
- If they said "Limited evidence provided" → Note: "We made claims without proof; need more case study metrics."
- If they said "Approach was too generic" → Note: "We must front-load project-specific context."

### Step 3 — Update the Win Themes
Based on what won and what lost, suggest specific updates to the `references/win-themes.md` file. For example, if we lost on sustainability, suggest strengthening the ESG win theme with harder metrics.

---

- [HUMAN INPUT REQUIRED] Do not invent project metrics, values, or outcomes. If data is missing, ask the user before drafting.

## Anti-Patterns (What NOT to do)
- DO NOT use a different structure. Always use the STAR method.
- DO NOT forget to incorporate win themes.
- DO NOT hallucinate project metrics or outcomes. Ask the user if data is missing.

## Quality Checks
- [ ] STAR method (Situation, Task, Action, Result) used for all case studies.
- [ ] Win themes from `Context/company.md` incorporated.
- [ ] No hallucinated metrics or project details.
- [ ] Debrief mode: score differential captured for every quality criterion.
