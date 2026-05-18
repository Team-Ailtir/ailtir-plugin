---
name: ailtir_bd_market-intelligence
description: "[BD] Build and maintain market-wide contractor profiles from public procurement data, match live tenders to profiled contractors, and seed the OrgProfile when a free-tier user converts to a paying customer. Invoke with /ailtir:ailtir_bd_market-intelligence."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Market-wide data assembly and intelligence engine. Ingests public procurement data, resolves contractor identities across fragmented records, builds structured Prospect Profiles, and matches live tenders to profiled contractors as a platform-level growth and onboarding tool.

## Scope

Does: ingest and normalise eTenders, TED, BCMS, and directory data; resolve contractor entities using CRO-anchored matching; assemble Prospect Profiles covering sector focus, geographic footprint, contract value range, authority relationships, and certifications; score tender-to-prospect match quality; capture free-tier behavioural signals; seed OrgProfiles on customer conversion.

Does NOT: access or process paying customers' internal data; make bid recommendations or score win probability; send emails or notifications directly; contact contractors or authorities; scrape sources requiring authentication; store individual contact details without explicit consent; perform customer-specific competitor analysis (that is `/ailtir:ailtir_bd_competitive-intelligence`).

## Instructions

1. **Load available public data sources.** Run:
   ```bash
   ailtir kb list
   ```
   Identify the contractor registry KB. Confirm which ingestion sources are active: eTenders CSV, TED API, BCMS CSV, Safe-T-Cert directory, VCR directory, and CIF directory. If the registry KB is empty or missing, inform the user: "The contractor registry must be seeded before this skill can produce useful output. Provide the relevant data files or confirm portal access."

2. **Ingest and normalise source records.** For each new data batch, normalise all records to a common schema: source, source ID, entity name, entity type, CRO number (if available), address, contract value, CPV codes, authority, and date. Validate each record; skip and log any row missing both entity name and CRO number.

3. **Resolve contractor entities (CRO-anchored).** Apply a layered matching approach against the registry:
   - Layer 1 — Exact CRO match (from TED BT-501 field): confidence 0.95
   - Layer 2 — Normalised name match (strip Ltd/DAC/PLC, normalise punctuation, case-insensitive): confidence 0.85
   - Layer 3 — Fuzzy name match with address proximity confirmation (same county): confidence 0.70
   - Layer 4 — Unresolved (below 60% confidence): flag for human review

   Do not auto-merge any entity when confidence is below 85%. Present candidates to the user: "Ambiguous match for [name] — confirm: Merge to Entity A, Merge to Entity B, Keep separate, or Flag for investigation?"

4. **Build or update Prospect Profiles.** For each resolved entity, assemble and incrementally maintain:
   - Identity: CRO number, legal name, trading names, legal form, status (Active/Dissolved), registered address
   - Sector profile: aggregate all contract awards by CPV division; calculate sector weight as percentage of total award value (minimum 3 awards before calculating percentages; below that, label "Insufficient data")
   - Geographic footprint: map award authority locations and BCMS project locations to NUTS regions; identify primary region
   - Contract value profile: calculate P25, median, P75, and max from award history (minimum 5 awards for reliable range)
   - Authority relationships: for each authority the contractor has won from, record contract count, total value, last award date, and a relationship strength score (0-100 based on recency and frequency)
   - Growth trajectory: annual award value trend classified as Growing (CAGR above 15%), Stable (0-15%), Declining (below 0%), or Insufficient data (fewer than 3 years)
   - Certifications: from directory scrapes — Safe-T-Cert, VCR, CIF membership, CIRI
   - Contact: company website and info@ email only (no named individuals at MVP)

   Score profile completeness 0.0-1.0 across dimensions: Rich (0.70+), Moderate (0.40-0.69), Sparse (below 0.40).

5. **Score tender-to-prospect matches.** When a new tender notice is received from `/ailtir:ailtir_bd_opportunity-intelligence`, score each active Prospect Profile on 7 dimensions:
   - Sector match (25%): Jaccard similarity between tender CPV divisions and profile sector history
   - Value fit (20%): Gaussian fit to the profile's contract value range; peak score when tender value falls between P25 and P75
   - Geographic match (15%): same NUTS region = 1.0, adjacent = 0.7, national = 0.4
   - Authority relationship (15%): prior win from this authority = 1.0, same authority type = 0.5, no history = 0.0
   - Procurement route fit (10%): high win count in this procedure = 1.0
   - Capacity estimate (10%): low recent award frequency suggests available capacity
   - Competitive intensity (5%): fewer matches for this tender = slightly higher score

   Thresholds: score of 0.80 or above = Strong match (daily brief); 0.60-0.79 = Good match (weekly digest); 0.40-0.59 = Moderate match (monthly report); below 0.40 = suppress.

6. **Generate tender match sets.** Compile the top 5-10 matches per contractor scoring 0.60 or above, sorted by score. For each match, include: tender title, authority, estimated value, deadline, match score, and the 2-3 dimensions that contributed most to the score (e.g., "Healthcare sector — your #1, Cork region — your base, HSE — won 3 previous").

7. **Capture and apply behavioural signals.** Log each free-tier engagement event: tender viewed, saved/bookmarked (strong positive), dismissed (negative), email clicked. Use saved and dismissed signals as implicit feedback to refine per-contractor matching weights over time. Flag a contractor as a Product-Qualified Lead (PQL) when their engagement score reaches 60+:
   - Login 3+ times per week: 20 points
   - 10+ tender views in 30 days: 20 points
   - Team invitation sent: 15 points
   - Document uploaded: 15 points
   - Pricing page visited: 15 points
   - 5+ saved tenders: 10 points
   - Shared tender with colleague: 5 points

   Inform the user when a contractor crosses the PQL threshold so the sales or growth team can be notified.

8. **Seed an OrgProfile on customer conversion.** When a free-tier user converts to a paying customer, export their Prospect Profile as a structured seed:
   ```bash
   ailtir kb chat <kb_id> "export prospect profile for <CRO number or registry ID>"
   ```
   Pass the seed to the onboarding flow: sector focus, geographic preferences, contract value range, authority relationships, and certifications. Inform the user: "Profile seed ready for onboarding. Customer should confirm or correct all pre-populated fields. Fields not available from public data — team capacity, preferred subcontractors, content library — will be collected during onboarding."

9. **Manage profile lifecycle.** Flag any profile with no new data for 18 months as "potentially inactive." For dissolved companies (CRO status check), mark as "Inactive — dissolved [date]", retain for historical analysis, and exclude from tender matching. For opt-out requests, add to the suppression list within 72 hours, remove from active matching, and retain only anonymised statistical data (sector, region, value — no identifying information).

10. **Handle false merge detection.** If a merged entity shows non-overlapping sectors, different registered addresses in widely separated counties, or conflicting director sets, flag as a potential false merge. Present to the user: "Possible false merge detected for [entity name] — confirm merge is correct, split into two entities, or flag for investigation."

## Error Handling

- **Exact same contractor name in different counties with no CRO overlap:** Keep separate; flag for manual review; present both profiles with distinguishing context; do not auto-merge.
- **Joint venture winner name in award data:** Parse into component entities; create a JV record linked to both parent profiles; attribute the award proportionally (50/50 unless stated otherwise).
- **Award value missing or zero:** Exclude from value-based calculations; include in count-based calculations (sector, authority); flag as "Value not disclosed."
- **BCMS builder name matches no CRO entity:** Store as an unresolved record; attempt re-resolution monthly as new entities enter the registry; do not create a phantom profile from unresolved BCMS data alone.
- **eTenders data format changes causing ingestion failure:** Alert the user; fall back to the last successful ingest; re-engineer the parser within 48 hours; log the gap period for data freshness reporting.
