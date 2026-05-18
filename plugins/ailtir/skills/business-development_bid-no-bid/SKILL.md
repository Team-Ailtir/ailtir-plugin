---
name: ailtir_bd_bid-no-bid
description: "[BD] Generate a structured Go/No-Bid scorecard for a tendering opportunity within 4 hours by applying deterministic disqualifier checks, win probability calculation, and margin analysis. Invoke with /ailtir:ailtir_bd_bid-no-bid."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Structured decision framework enforcer for Go/No-Bid decisions. Applies deterministic logic and statistical models to generate a scorecard and recommendation; the Director makes the final call.

## Scope

Does: validate credentials, financial capacity, and team capacity; calculate win probability; analyse expected margin; score strategic fit; produce sensitivity scenarios; deliver a structured recommendation narrative.

Does NOT: make the final Go/No-Bid decision; read full ITT documents; draft technical content; contact procurement authorities; override mandatory disqualifiers without an explicit Director override log.

## Instructions

1. **Load the contractor profile and configuration.** Run:
   ```bash
   ailtir profile get
   ```
   Extract: sector focus with weights, geographic preference, contract value sweet spot, financial ceiling (max single contract and max total concurrent), minimum margin requirement (%), risk appetite threshold (Conservative ≥35% win prob / Balanced ≥25% / Aggressive ≥15%), team capacity (Bid Manager, Cost Manager, Technical Lead available hours), and any exclusion rules. If configuration is missing or incomplete, stop and ask the user to configure these settings before proceeding.

2. **Obtain the opportunity brief.** Ask the user to provide one of: a structured brief from `/ailtir:ailtir_bd_opportunity-intelligence`, a portal URL, or pasted notice text. Extract: title, contracting authority, CPV codes, estimated value, procurement route, evaluation method, programme duration, location, submission deadline, and the strategic fit score from opportunity intelligence if available.

3. **Run mandatory disqualifier checks (credential validation).** Run:
   ```bash
   ailtir kb chat <kb_id> "required certifications for CPV <codes>"
   ```
   Cross-reference the contractor's active credentials against the mandatory requirements for each CPV code. If any required credential is missing or expires before the submission deadline, set Disqualifier = FAIL and inform the user: "No-Bid recommended unless credentials are obtained before deadline — [credential name], remediation deadline: [date]."

4. **Run mandatory disqualifier checks (financial capacity).** Calculate: current active contract exposure + this opportunity value. If the total exceeds the contractor's single-contract ceiling or total concurrent ceiling, set Disqualifier = FAIL and inform the user: "Exceeds financial capacity ceiling by [€X]. No-Bid unless ceiling is raised by Director."

5. **Run mandatory disqualifier checks (team capacity).** Estimate resource demand: Bid Manager ~40 hours, Cost Manager ~60 hours, Technical Lead ~80 hours over ~6 weeks. Compare against available capacity. If any role has zero availability, set Disqualifier = FAIL. If buffer is below 5 hours/week per role, set WARNING. Stop and confirm with the user: "Team capacity is [tight / insufficient]. Confirm whether to proceed or deprioritise an existing bid."

6. **If any mandatory disqualifier is FAIL**, present the full disqualifier details and stop. Ask the user: "Accept No-Bid, Override and proceed (log reason), or Remediate and re-score?"

7. **Calculate win probability.** Start from the contractor's historical win rate in the same sector and value band:
   ```bash
   ailtir kb chat <kb_id> "historical win rate for sector <sector> value band <range>"
   ```
   Apply adjustments: authority relationship strength from `/ailtir:ailtir_bd_relationship-intelligence` (+5% score ≥70, +3% score 40-69, +0% score <40); strategic fit score (+2% if ≥80, +0% if 60-79, -3% if <60); procurement route (+3% restricted, +5% negotiated with prior relationship, -2% negotiated new authority); evaluation method (+3% MEAT if strong technical credentials, -3% if weak). Express result with confidence interval (e.g., "29% ±8%"). If fewer than 5 historical bids exist in the category, label confidence LOW and use market benchmarks as baseline.

8. **Analyse expected margin.** Run:
   ```bash
   ailtir kb chat <kb_id> "historical margin for sector <sector> authority <authority>"
   ```
   Adjust for: new authority discount expectation (-1-2%), competitive intensity, and risk reserve (1-3%). Compare against the minimum margin requirement from the contractor profile. If expected margin is below minimum, set flag "Margin below threshold."

9. **Score strategic fit (0-100).** Combine: sector alignment (up to 25 pts), geographic alignment (up to 20 pts), contract value fit (up to 20 pts), procurement route fit (up to 15 pts), team capacity buffer (up to 10 pts), and relationship potential from `/ailtir:ailtir_bd_relationship-intelligence` (up to 10 pts).

10. **Generate the Go/No-Bid recommendation.** Apply decision logic:
    - Any FAIL disqualifier → "No-Bid (mandatory disqualifier)"
    - Win probability below risk appetite threshold → "No-Bid (low win probability)"
    - Expected margin below minimum → "No-Bid (margin below minimum)"
    - Strategic fit below 60 → "Caution: consider No-Bid (weak strategic fit)"
    - Capacity WARNING but resources available → "Go (with capacity flag)"
    - All checks pass → "Go"

    Stop and confirm with the user: "Recommendation is [Go / No-Bid / Caution]. Full scorecard shown below. Do you approve, override, or request additional analysis?"

11. **Present sensitivity scenarios.** Show 3-4 what-if cases such as: "If minimum margin lowered from X% to Y%, recommendation changes to Go"; "If credentials obtained before deadline, disqualifier clears"; "If team frees capacity next month, this bid can be reprioritised."

12. **Pre-populate the risk register.** Based on CPV codes and opportunity profile, flag likely risk categories: credential/compliance, scope/specification, commercial, and technical. Inform the user: "Run `/ailtir:ailtir_bd_opportunity-intelligence` or your contract risk workflow to develop these further."

## Error Handling

- **Missing historical bid data:** Use market benchmarks as baseline; label confidence LOW (±15%); recommend Director manual review.
- **Financial thresholds not configured:** Block scorecard and ask the user to set minimum margin, financial ceiling, and risk appetite in the contractor profile before proceeding.
- **Team capacity data unavailable:** Assume capacity is available but flag "Resource data unavailable — Bid Manager must confirm before Go decision."
- **Opportunity brief incomplete (missing CPV, value, or deadline):** Refuse to score; return to the user with a list of the missing fields required.
- **Director override requested:** Accept override; log Director name, reason, and timestamp; flag bid for closer monitoring checkpoints during execution.
