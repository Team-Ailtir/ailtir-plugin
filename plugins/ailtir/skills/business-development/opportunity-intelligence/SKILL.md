---
name: opportunity-intelligence
description: "[BD] Score a procurement notice against your Tender Fit Profile and generate a Pre-Market Engagement Brief for PIN-stage opportunities. Invoke with /ailtir:opportunity-intelligence."
argument-hint: ""
allowed-tools: Bash
---

Market scout for construction tendering. Takes a contract notice (URL or PDF), scores it against the contractor's strategic profile, and routes qualified opportunities to the Bid/No-Bid queue.

## Scope

Does: ingest notice data, apply strategic fit scoring (0–100), generate Pre-Market Engagement Briefs for PINs, confirm routing decisions with the user.

Does NOT: make Go/No-Bid decisions, read full ITT documentation, contact procurement authorities, score win probability, or perform competitor analysis.

## Instructions

1. **Load the strategic profile.** Run:
   ```bash
   ailtir profile get
   ```
   Extract: sector focus with weights, geographic preference, contract value sweet spot (min/max), preferred procurement routes, team capacity (max concurrent bids and active bid count), and any exclusion rules. If the profile is empty or missing, stop and prompt: "Your Tender Fit Profile is not set up. Run `/ailtir:onboarding` first."

2. **Obtain the contract notice.** Ask the user to provide one of:
   - A portal URL (eTenders, TED EU, Find a Tender, eTendersNI)
   - Pasted notice text
   - A path to a notice PDF

3. **Extract structured fields.** From the notice, identify:
   - Title, contracting authority, authority type
   - CPV codes, estimated value (min/max, currency)
   - Procurement route (open / restricted / negotiated / framework)
   - Submission deadline, clarification deadline
   - Location, description snippet, documentation URL
   - Whether this is a Prior Information Notice (PIN) or a Contract Notice

   Flag any missing required fields (deadline, authority, or value) as "Incomplete Notice — do not route without manual review."

4. **Apply mandatory disqualifications first** (before scoring):
   - If the opportunity matches an exclusion rule → score = 0, label "Disqualified by exclusion rule", stop routing.
   - If a mandatory certification is required but missing (based on CPV or description) → score = 0, label "Missing mandatory credential."
   - If estimated value exceeds the contractor's financial capacity ceiling → score = 0, label "Exceeds capacity ceiling."

5. **Calculate strategic fit score (0–100).** Apply these weighted components:
   - **Sector match** (max 25 pts): primary sector = 25, secondary = 15, no match = 5
   - **Location preference** (max 20 pts): preferred region = 20, secondary = 10, other = 5
   - **Contract value** (max 20 pts): within sweet spot = 20, 20–50% outside = 10, 50%+ outside = 3, exceeds upper capacity = 0 + flag
   - **Procurement route** (max 15 pts): preferred = 15, acceptable = 10, unpreferred = 3
   - **Team capacity** (max 10 pts): capacity available = 10, at capacity = −10 + flag

   If more than 2 required fields are missing, reduce the total by 10% and note "Low confidence — incomplete notice."

6. **Present the scoring breakdown.** Show each component and its points, total score, and a one-paragraph plain-English summary (e.g., "Score: 85/100 — strong healthcare sector match (25 pts), preferred Dublin location (20 pts)..."). Ask the user to confirm the result before proceeding.

7. **Handle PIN-stage notices.** If the notice is a Prior Information Notice:
   - Flag as PIN, priority HIGH.
   - If score ≥ 70, generate a Pre-Market Engagement Brief:
     - Run `ailtir kb chat <kb_id> "authority profile and past procurement history for <authority name>"` to retrieve relationship history and past procurement patterns.
     - Summarise: authority name/type, prior relationship (projects or "No prior relationship"), typical contract value/procurement route patterns, engagement timeline ("PIN published [date]. RFQ expected [estimate]. Window: [weeks] remaining.").
     - Suggest engagement actions: technical site visit, RFI submission, pre-qualification meeting.
   - Present the brief and ask: "Pursue pre-market engagement (~10 hours), Monitor only, or Ignore?"
   - Record the decision in the conversation.

8. **Route qualified Contract Notices.** For non-PIN notices with score ≥ 70:
   - Confirm with the user: "Route this opportunity to the Bid/No-Bid queue? (SLA: scorecard due within 3 days)"
   - On confirmation, remind: "Run `/ailtir:bid-no-bid` to evaluate this opportunity."

9. **Handle borderline scores (40–69).** Present with the note "Below threshold — manual review recommended" and ask: "Include despite low score? (Requires explicit confirmation.)"

10. **Batch processing.** If the user provides multiple notices, process steps 2–9 for each, then show a summary: total reviewed, score distribution, top 3 by score, disqualified count.

## Error Handling

- **Profile not found:** Stop and direct to `/ailtir:onboarding` before scoring.
- **Incomplete notice (missing deadline or authority):** Present with caveat, do not auto-route; offer to proceed after manual data entry.
- **Duplicate detected** (same authority + deadline already in queue): Warn "This appears to match an existing opportunity — confirm before routing."
- **Capacity at maximum:** Note "Team at capacity. Hold this opportunity and run `/ailtir:orchestrator` to review active bids."
- **PDF extraction poor quality:** If fewer than 5 key fields extracted, ask the user to paste the notice text directly.
