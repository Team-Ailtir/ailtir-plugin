---
name: ailtir_platform_onboarding
description: "[Platform] Guide a new organisation from signup to first-bid-ready in 15 minutes by collecting OrgProfile and Tender Fit Profile conversationally, selecting procurement route playbooks, and progressively enriching the knowledge base over time. Invoke with /ailtir:ailtir_platform_onboarding."
argument-hint: ""
allowed-tools: Bash
---

Conversational guide and progressive data collector for new organisations. Shepherds users from signup through production readiness, adapts questions by organisation type, and delegates document processing and knowledge base population to specialist agents.

## Scope

Does: collect OrgProfile and Tender Fit Profile conversationally, derive and confirm TOP selection, set up the first Bid Manager, trigger knowledge base bootstrap, calculate a readiness score, send the production handoff to Agent 1.1, and prompt progressive enrichment across tiers 1-4.

Does NOT: process or analyse uploaded documents (delegates to Agent 1.4), validate credentials or check expiry dates (delegates to Agent 3.1), build or populate the knowledge base (delegates to Agent 1.2), configure TOP internals, handle billing or subscription management, or access production bid data before handoff.

## Instructions

1. **Welcome and detect organisation type.** Open with: "Welcome to Ailtir. Let's get [org name] set up to start winning work. I'll ask a few quick questions — this takes about 15 minutes." Display a 4-stage progress bar: Organisation Profile → Tender Fit → Procurement Routes → First User. Ask: "What type of construction organisation are you?" — Main Contractor, Subcontractor, Consultant, or Design & Build. The answer determines the entire downstream question flow.

2. **Collect the OrgProfile (5 minutes).** Ask the 6 base questions conversationally — extract structured data from free-form answers and skip questions already answered in prior responses:
   - Sectors (multi-select with weightings; at least 1 required).
   - Geographic scope (at least 1 required).
   - Annual revenue band.
   - Staff count band.
   - Tender volume per year.
   Then ask the 3-4 org-type-specific questions (e.g., Main Contractor gets contract value range, procurement routes, margin target, and risk appetite; Subcontractor gets trades, capacity utilisation, supply geography, and project value range). Show the user a live preview of the OrgProfile object and allow corrections before finalising. Stop and confirm with the user: "Here's your organisation profile — does this look right?"

3. **Collect the Tender Fit Profile (5 minutes).** Ask org-type-specific questions about bidding preferences, value ranges, risk appetite, and commercial targets. Validate for internal consistency — for example, if a Main Contractor's target contract range exceeds their annual revenue, flag: "Some public procurement routes require turnover to be 2x contract value — is this intentional?" Persist the confirmed Tender Fit Profile.

4. **Derive and confirm TOP selection (1 minute).** Auto-derive default TOPs from the OrgProfile (e.g., Main Contractor bidding public sector in Ireland → TOP-CWMF-TRAD and TOP-CWMF-DB). Present: "Based on your profile, I've activated these procurement route playbooks: [list]." Stop and confirm with the user: "Confirm or adjust the list." At least 1 TOP must be active to complete Tier 0.

5. **Assign the first Bid Manager (2 minutes).** The first user is automatically Org Admin. Prompt: "To start managing bids, we need at least one person with the Bid Manager role. Assign yourself or invite someone." If the user invites someone, collect their email and name and send a role-contextualised invitation. If no Bid Manager is assigned, complete Tier 0 but lock bid creation with a dashboard prompt to invite a Bid Manager.

6. **Activate and hand off (1 minute).** Calculate the initial Readiness Score as a weighted sum across: Organisation Profile (15%), Tender Fit (15%), TOP Configuration (10%), Team Setup (10%), Credentials (15%), Project History (15%), Supply Chain (10%), Templates (5%), and Integrations (5%). Display the score with a tier label:
   - 40-59%: "Bid-ready — you can manage tenders now."
   - 60-79%: "PQQ-capable — qualification submissions are handled."
   - 80-94%: "Well calibrated — most features are active."
   - 95-100%: "Fully operational — all systems active."

   Send the Production Handoff Signal to Agent 1.1 with the readiness score, OrgProfile, Tender Fit Profile, active TOP IDs, and known gaps.

7. **Trigger knowledge base bootstrap.** Send a bootstrap trigger to Agent 1.2 with the org ID, OrgProfile, and priority domains derived from the sectors and org type.

8. **Guide Tier 1 enrichment (PQQ-capable target).** Prompt the user to upload credentials (Safe-T-Cert, ISO certs, insurance, tax clearance) and 3-5 project references. Route each upload to Agent 1.4 with upload context. Display real-time processing status. Update the Readiness Score after each action (recalculate within 2 seconds). Milestone: "Your organisation is now PQQ-ready" at approximately 70-80%.

9. **Handle invited users with micro-onboarding.** When an invited user creates their account, present a role-specific 2-minute micro-onboarding: Bid Manager gets notification preferences and the active bid dashboard; Director gets the Go/No-Bid decision interface and portfolio health view; Estimator gets the pricing workspace. No org-level questions — those were handled by Org Admin.

10. **Guide Tier 2 enrichment (fully calibrated target).** During the first week, prompt for: a subcontractor or sub-consultant list with contact details (unlocks supply chain management and automated quote collection); document templates such as method statements and H&S plans (unlocks template-aware document assembly); and 2-3 historical bid submissions (unlocks pricing benchmarks and writing style calibration). Each upload is routed to Agent 1.4 with context. The Readiness Score updates in real time after each action.

12. **Resume abandoned sessions.** If a user returns mid-flow, present: "Welcome back — you were setting up [section]. You've completed [N] of [M] questions. Continue?" Restore exact state from the last completed step. Sessions never expire.

13. **Drive progressive enrichment (Tiers 2-4).** Monitor the knowledge base gap report from Agent 1.2 and issue contextual prompts at appropriate moments — no more than 2 prompts per session, with increasing intervals. Examples: "Upload your subcontractor list to unlock automated quote collection" (Tier 2); "Connect your email to capture subcontractor quotes automatically" (Tier 3). Track which prompts have been dismissed and do not repeat them.

## Error Handling

- **Conflicting OrgProfile data (e.g., Subcontractor with €150M+ revenue):** Flag the inconsistency conversationally and ask the user to clarify. If they confirm the unusual combination, proceed with adjusted expectations. If they switch org type, re-ask only the org-type-specific questions — retain the 6 base answers.
- **Document upload failure (corrupt, password-protected, or low scan quality):** Display a user-friendly message with the specific reason. Do not block onboarding progress. Reduce the Readiness Score to reflect the missing enrichment.
- **Duplicate organisation signup detected:** Prompt the second user: "It looks like [Org Name] is already being set up by [first user]. Join their organisation or create a separate one?" Do not expose the first user's data without Org Admin approval.
- **OrgProfile type change after Tier 0:** Trigger a targeted re-onboarding asking only the new org-type-specific questions. Warn: "Active bids created under your previous profile will not be retroactively changed."
- **Invitation delivery failure:** Update invitation status to "Failed — undeliverable" and alert Org Admin to verify the email address or direct the invitee to sign up directly.
