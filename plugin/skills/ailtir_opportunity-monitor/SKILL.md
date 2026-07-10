---
name: ailtir_opportunity-monitor
description: Automated daily background task that checks your email for tender alerts appropriate to your active Ailtir profile (Irish eTenders/TED or UK Find a Tender/Contracts Finder), scores each opportunity against your company profile using a 5-dimension strategic fit model, and logs qualified leads to your Notion Bid Pipeline.
---

# Ailtir Opportunity Monitor

## Usage Reporting

Before doing workflow-specific work, call the `plugin_report_usage` tool from
the bundled `ailtir` MCP server with these arguments:

- `skill_name`: `ailtir_opportunity-monitor`
- `plugin_version`: `2.15.1`

If reporting returns `failed`, leave the failure visible and continue the workflow.

You are an automated Bid Intelligence Agent running as a scheduled daily task. Your role is to act as the company's first filter on the market — surfacing the right opportunities, scoring them with rigour, and routing the best ones to the Bid Pipeline before the team arrives at their desks.

## Context Files Required

Before running, read the following files from the user's workspace:

- `Context/profile.json` — Determines which market to monitor (`ireland-gc` or `uk-gc`) and which reference / parser files to load.
- `Context/company.md` — Company profile, target sectors, preferred regions, contract value sweet spot, active certifications.
- `Context/connectors.md` — Connector status for email and Notion.

If `Context/profile.json` is missing, stop and tell the user to run `/ailtir-cowork-plugin:ailtir_setup`.

---

## Step 1: Fetch Tender Alert Emails

Use the email connector to search the inbox for tender alert messages received in the last 24 hours. The search terms depend on `profile_key`:

**Under `ireland-gc`:**
- From: `etenders@eu-supply.com` OR `notifications@etenders.gov.ie` OR `noreply@ted.europa.eu`
- Subject contains: `eTenders Daily Alert` OR `Contract Notice` OR `OJEU` OR `TED` OR `Prior Information Notice`
- Parse each email using `scripts/parse_etenders_email.py` from this skill's directory.

**Under `uk-gc`:**
- From: `no-reply@find-tender.service.gov.uk` OR `alerts@contractsfinder.service.gov.uk`
- Subject contains: `Find a Tender` OR `Contracts Finder` OR `Tender Notice` OR `Preliminary Market Engagement` OR `Contract Award Notice` OR `Contract Details Notice`
- Parse each email using `scripts/parse_fts_email.py` from this skill's directory.

If no matching emails are found, send the user a brief message: "Daily Tender Check: No new alerts received in the last 24 hours." Then stop.

---

## Step 2: Extract Structured Data from Each Notice

For each notice found, extract the following fields. If a field is not present in the email, mark it as `Unknown`:

| Field | Notes |
|---|---|
| **Title** | Full contract title |
| **Authority** | Contracting authority name |
| **Authority Type** | `ireland-gc`: Central Government / Local Authority / HSE / Education / Semi-State / Private. `uk-gc`: Central Government / Local Authority / NHS / Education / Devolved / Utility / Private. |
| **Estimated Value** | Use the currency of the profile — EUR for `ireland-gc`, GBP for `uk-gc`. If a range is given, use the midpoint. |
| **CPV Codes** | All listed CPV codes |
| **Deadline** | Submission deadline date |
| **Procurement Route** | `ireland-gc`: Open / Restricted / Competitive Dialogue / Negotiated / Framework Call-Off / Unknown. `uk-gc` (Procurement Act 2023): Open Procedure / Competitive Flexible Procedure / Direct Award / Framework Call-Off / Dynamic Market / Unknown. |
| **Notice Type** | `ireland-gc`: Contract Notice / Prior Information Notice (PIN) / Contract Award Notice. `uk-gc`: Tender Notice / Preliminary Market Engagement Notice / Pipeline Notice / Transparency Notice / Contract Award Notice / Contract Details Notice. |
| **Portal Link** | Direct URL to the notice |
| **Location** | County / region of works |

---

## Step 3: Apply Mandatory Disqualification Gates

Before scoring, apply the following hard gates. If any gate is triggered, mark the opportunity as `DISQUALIFIED` with the reason, and do not score it further.

**Gate 1 — Missing Mandatory Certifications:**
- Cross-reference the CPV codes and description against the certifications listed in `Context/company.md`.
- Under `ireland-gc`: If the notice explicitly requires CIRI registration (works >€50k), Safe-T-Cert, ISO 9001, or another credential the company does not hold, mark as `DISQUALIFIED: Missing credential — [certification name]`.
- Under `uk-gc`: If the notice explicitly requires SSIP membership (CHAS, SafeContractor, Constructionline Gold, or Achilles Building Confidence), ISO 9001/14001/45001, Building Safety Act competency (HRB scope), or a current Modern Slavery s.54 statement (contracting authority may require) the company does not hold, mark as `DISQUALIFIED: Missing credential — [certification name]`.

**Gate 2 — Exceeds Financial Capacity:**
- If the estimated value exceeds the company's declared financial capacity ceiling in `Context/company.md`, mark as `DISQUALIFIED: Exceeds capacity ceiling`.

**Gate 3 — Exclusion Rules:**
- If the company has declared any exclusion rules in `Context/company.md` (e.g., "Exclude all demolition-only contracts", "Exclude contracts <€250k"), apply them here.

**Gate 4 — Post-Award / Transparency Notices:**
- Under `ireland-gc`: if the notice type is `Contract Award Notice`, do not score for pursuit.
- Under `uk-gc`: if the notice type is `Contract Award Notice` (pre-award), `Contract Details Notice` (post-award), or `Contract Termination Notice`, do not score for pursuit.
- In either case, log the notice separately as **Competitor Intelligence** — extract the winner name and contract value and note it in the Notion CRM under the relevant authority record.

---

## Step 4: Score Each Remaining Opportunity (0–100)

Apply the following 5-dimension scoring model to each opportunity that passed the gates. Read the scoring weights and reference tables from `references/{profile_key}/scoring-model.md` in this skill's directory.

### Dimension 1 — Sector Match (max 25 points)
Compare the opportunity's CPV codes against the company's declared primary and secondary sectors in `Context/company.md`.
- Primary sector match: **25 points**
- Secondary sector match: **15 points**
- No match / tertiary: **5 points**

### Dimension 2 — Geographic Preference (max 20 points)
Compare the location of works against the company's preferred and secondary regions.
- Preferred region: **20 points**
- Secondary region: **10 points**
- Outside preferred regions: **5 points**
- Unknown location: **10 points** (neutral; do not penalise missing data)

### Dimension 3 — Contract Value Fit (max 20 points)
Compare the estimated value against the company's declared sweet spot range in `Context/company.md`.
- Within sweet spot: **20 points**
- 20–50% below sweet spot: **10 points**
- 50%+ below sweet spot: **3 points**
- 20–50% above sweet spot: **10 points**
- 50%+ above sweet spot (capacity concern): **0 points** — flag "Value above sweet spot; check capacity"
- Unknown value: **10 points** (neutral)

### Dimension 4 — Procurement Route Preference (max 15 points)
Compare the procurement route against the company's preferences in `Context/company.md`.
- Preferred route (typically Open or Restricted): **15 points**
- Acceptable route: **10 points**
- Unpreferred route (e.g., Competitive Dialogue): **3 points**
- Unknown route: **10 points** (neutral)

### Dimension 5 — Notice Type Bonus (max 10 points)

**Under `ireland-gc`:**
- Contract Notice (live tender): **10 points** — actionable now
- Prior Information Notice (PIN): **10 points** — flag as PIN; high strategic value for pre-market engagement
- Unknown: **5 points**

**Under `uk-gc` (Procurement Act 2023 notice types):**
- Tender Notice (live opportunity): **10 points** — actionable now
- Preliminary Market Engagement Notice (PMEN): **10 points** — flag as PMEN; high strategic value for pre-market engagement
- Pipeline Notice: **7 points** — 12-month look-ahead; strategic
- Unknown: **5 points**

### Specification Bias Check (Qualitative Flag — no score impact)
Scan the notice title and description for signals that the specification may be written around an incumbent or a specific supplier:
- Unusually specific brand references or proprietary system names
- Extremely narrow technical requirements that match only one or two contractors
- Very short tender period (less than 10 working days for a complex contract)

If any of these signals are present, add a flag: `⚠️ Possible specification bias — review before committing resources`.

---

## Step 5: Classify Each Opportunity

Based on the total score:

| Score | Classification | Action |
|---|---|---|
| 70–100 | **MATCH** | Log to Notion Bid Pipeline; trigger Bid/No-Bid review |
| 40–69 | **MAYBE** | Log to Notion Bid Pipeline with lower priority |
| 0–39 | **IGNORE** | Do not log; include in summary count only |
| DISQUALIFIED | **DISQUALIFIED** | Do not log to pipeline; log to audit trail |

**Special handling for pre-market notices scoring ≥70:**
- Under `ireland-gc`: for a Prior Information Notice, log to Bid Pipeline with Status `0. PIN — Pre-Market Engagement` and use the template at `references/ireland-gc/pin-engagement-template.md`.
- Under `uk-gc`: for a Preliminary Market Engagement Notice, log to Bid Pipeline with Status `0. PMEN — Pre-Market Engagement` and use the template at `references/uk-gc/pin-engagement-template.md`.
- Add a note: "[Notice type] published [date]. Estimated Tender Notice release: [date + 3–12 months]. Pre-market engagement window open."
- This is a strategic relationship-building opportunity, not an immediate bid.

---

## Step 6: Log to Notion Bid Pipeline

For every MATCH and MAYBE opportunity, create a new record in the Notion Bid Pipeline database with the following fields populated:

| Notion Field | Value |
|---|---|
| Name | [Contract Title] |
| Status | `1. Lead Identified` (or `0. PIN — Pre-Market Engagement` / `0. PMEN — Pre-Market Engagement` for pre-market notices) |
| Authority | [Authority Name] |
| Estimated Value | [Value in the profile's currency: EUR for `ireland-gc`, GBP for `uk-gc`] |
| Deadline | [Deadline Date] |
| Strategic Fit Score | [Score / 100] |
| Source | `eTenders Alert` / `TED Alert` / `Find a Tender Alert` / `Contracts Finder Alert` (whichever the notice came from) |
| Portal Link | [URL] |
| CPV Codes | [Comma-separated list] |
| Notes | [Any flags: bias warning, capacity alert, missing data] |

If the Notion connector is unavailable, save the results to a local Markdown file at `Context/notion-cache/opportunity-log-[date].md` and notify the user.

---

## Step 7: Log Competitor Intelligence

For any Contract Award Notices found in Step 3 (Gate 4), update the Notion CRM:
- Find or create a record for the contracting authority.
- Add a note under "Award History": `[Date] — [Contract Title] awarded to [Winner] for [Value]`.

This builds the company's intelligence on which competitors are active with which authorities.

---

## Step 8: Send Daily Summary

Send the user a concise daily briefing:

```
📋 Ailtir Daily Tender Check — [Date]

Notices reviewed: [total]
MATCH: [n] opportunities logged to pipeline
MAYBE: [n] opportunities logged to pipeline
DISQUALIFIED: [n] (reasons: [brief list])
IGNORED: [n]

Top match today: [Title] — [Authority] — [Value with the profile's currency symbol: €X for `ireland-gc`, £X for `uk-gc`] — Score: [n]/100
[Portal Link]

[Any PIN alerts or bias flags]
```

---

- [HUMAN INPUT REQUIRED] If the email connector is unavailable, ask the user to forward the eTenders digest manually before proceeding.

## Anti-Patterns (What NOT to do)

- **DO NOT log every notice to the pipeline.** The filter is the entire point. A pipeline full of irrelevant leads is worse than no pipeline.
- **DO NOT score Contract Award Notices** — they are competitor intelligence, not pursuit opportunities.
- **DO NOT fail silently.** If the email connector returns no results, confirm this explicitly to the user rather than sending an empty summary.
- **DO NOT apply the specification bias flag as a disqualification.** It is an advisory flag only — the Bid Manager decides whether to pursue.
- **DO NOT prompt the user for input during the run.** This is a scheduled background task and must operate fully autonomously.
- **DO NOT create duplicate Notion records.** Before creating a new pipeline entry, check if the portal link already exists in the database.

## Quality Checks
- [ ] `Context/profile.json` read; correct `profile_key` parser and reference files loaded.
- [ ] All 4 mandatory disqualification gates applied before scoring.
- [ ] Score calculated using all 5 dimensions from `references/{profile_key}/scoring-model.md`.
- [ ] MATCH opportunities logged to Notion Bid Pipeline with correct CPV code and deadline.
- [ ] Estimated Values recorded in the profile's currency (EUR for `ireland-gc`, GBP for `uk-gc`).
- [ ] Daily summary sent to user with clear MATCH / MAYBE / PASS breakdown.
