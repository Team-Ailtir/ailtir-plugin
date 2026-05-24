---
name: ailtir_bd_relationship-intelligence
description: "[BD] Maintain the contractor's stakeholder contact graph, score relationship health, surface warm introduction paths for opportunities, and generate proactive engagement recommendations. Invoke with /ailtir:ailtir_bd_relationship-intelligence."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Strategic relationship advisor and institutional memory keeper. Tracks all interactions with contracting authorities and key individuals, scores relationship strength, and recommends engagement activities aligned with the active bid pipeline.

## Scope

Does: ingest and deduplicate contacts; log interactions by form or voice transcript; score relationship strength (0-100) per contact and per organisation; match contacts to pipeline opportunities; generate engagement recommendations; enforce GDPR consent checks.

Does NOT: contact stakeholders directly or send communications; make Go/No-Bid decisions; scrape personal data from social media; store health, political, or other special-category data; replace the BD Manager's judgement on relationship quality.

## Instructions

1. **Load the contractor profile and active pipeline.** Run:
   ```bash
   ailtir profiles get
   ```
   Then run:
   ```bash
   ailtir kbs list
   ```
   Identify the relationship intelligence KB. If none exists, ask the user to set one up before proceeding.

2. **Determine the task.** Ask the user which action is needed:
   - Add or update a contact
   - Log an interaction (form or voice)
   - Get relationship context for an opportunity
   - Review engagement recommendations
   - Run a GDPR consent check or erasure

3. **Add or update a contact.** Collect: full name, organisation, role/title, and optionally email, phone, and notes. Before storing, check GDPR consent status:
   ```bash
   ailtir kbs chat <kb_id> "consent status for <name> at <organisation>"
   ```
   If no consent record exists, store only name and organisation under legitimate interest basis and flag as "Pending Consent." Run fuzzy deduplication: if a contact with more than 85% name similarity at the same organisation already exists, stop and confirm with the user: "Possible duplicate found — merge, keep separate, or delete?"

4. **Log an interaction.** Accept input as a structured form or a voice transcript. From either source, extract: contact name(s), organisation, date, interaction type (meeting, call, event, pre-tender, site visit, etc.), summary notes, sentiment (positive/neutral/negative), and any follow-up actions with suggested due dates. Stop and confirm with the user: "Confirm extracted interaction details before saving."

5. **Calculate relationship strength scores.** For each contact involved in or queried about an opportunity:
   - Recency (0-30 pts): last interaction within 30 days = 30, 31-60 = 25, 61-90 = 20, 91-180 = 10, 181-365 = 5, over 365 = 0
   - Frequency (0-25 pts): 6+ interactions in 12 months = 25, 4-5 = 20, 2-3 = 15, 1 = 5
   - Depth (0-25 pts): face-to-face meeting +10, pre-tender/framework discussion +8, completed project together +7, event only +3
   - Sentiment (0-10 pts): positive average = 10, neutral = 5, negative = 0
   - Seniority (0-10 pts): decision-maker +10, influencer +7, operational +4, peer +2
   - Cap event-only contacts at 10 frequency points maximum.

   Organisation score = (best contact score × 0.6) + (min(contacts above 40 × 10, 40) × 0.4).

6. **Match contacts to an opportunity.** When given an authority name or opportunity ID, run:
   ```bash
   ailtir kbs chat <kb_id> "contacts at <authority>"
   ```
   If contacts are found, generate a stakeholder map: names, roles, scores, last interaction dates, and recommended approach per contact. If no direct contacts exist, search for indirect connections (people who previously worked at the authority, or design team contacts linked to the project). If no connections at all, report "Cold opportunity — no relationship intelligence available" and suggest relevant networking events.

7. **Identify relationship decay.** Flag contacts where the recency component has fallen below threshold: 60 days for contacts with a prior score above 70, 90 days for others, 180 days for all others. Report status as Active, At Risk (amber), or Dormant (red).

8. **Generate engagement recommendations.** For each At Risk or pipeline-relevant contact, produce a specific recommendation:
   - High-value contact (score was above 70): "Schedule coffee meeting with [Name]. Last discussed [topic] on [date]."
   - Medium contact (score 40-70): "Send project update email referencing [shared project or event]."
   - Pipeline opportunity within 60 days and relationship score below 50: "Proactive engagement recommended — request pre-tender meeting."
   - PIN-stage opportunity: "Framework renewal for [authority] expected [quarter]. Recommend scheduling capability presentation within 30 days."

   Stop and confirm with the user: "Review engagement recommendations — accept, modify, dismiss, or reassign?"

9. **Handle GDPR requests.** For a consent withdrawal or erasure request:
   - Immediately cease processing the contact's data.
   - Remove from all active stakeholder maps and opportunity briefs.
   - Inform the user: "Contact [Name] removed. Stakeholder map for [opportunity] updated — gap created."
   - If the contact is linked to an active bid, note: "Recommend direct approach without system support for this contact."

10. **Deliver relationship context to other skills.** When called by `/ailtir:ailtir_bd_opportunity-intelligence` or `/ailtir:ailtir_bd_bid-no-bid`, return: organisation relationship score (0-100), key contacts with individual scores, last interaction dates, risk factors (e.g., "No decision-maker contact"), and a one-paragraph engagement recommendation.

## Error Handling

- **Voice transcript unrecognisable (confidence below 50% on name/organisation):** Reject automated extraction; present raw transcript to the user and ask them to enter data manually or re-record.
- **Bulk CSV import with more than 20% invalid rows:** Reject the entire import; show a validation report breaking down the issues; offer "Import valid rows only" or "Fix and re-upload."
- **GDPR erasure for contact linked to active bid:** Execute erasure immediately (GDPR requirement overrides operational convenience); notify the BD Manager of the gap created in the stakeholder map.
- **Two BD Managers claim the same authority relationship:** Present the conflict to the Director and ask them to designate a primary owner; allow secondary owner designation.
- **Contact graph empty for queried authority:** Return a structured "no relationship intelligence" response; suggest the nearest networking event or introduction path as a starting point.
