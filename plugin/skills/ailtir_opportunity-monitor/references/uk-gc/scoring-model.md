# Ailtir Opportunity Scoring Model — UK General Contractor

This reference file defines the 5-dimension strategic fit scoring model used by the Opportunity Monitor for the UK market. Structure is common with the Irish profile; the code tables, thresholds, and alert sources reflect the UK Procurement Act 2023 regime.

## Scoring Dimensions

| Dimension | Max Points | Description |
|---|---|---|
| Sector Match | 25 | CPV code alignment with company's declared sector focus |
| Geographic Preference | 20 | Location of works vs. company's preferred regions |
| Contract Value Fit | 20 | Estimated value vs. company's sweet spot range |
| Procurement Route | 15 | Route type vs. company's preferred procurement routes |
| Notice Type Bonus | 10 | Live Tender Notice, Preliminary Market Engagement Notice, or Transparency Notice |
| **Total** | **90** | **Score out of 90; normalised to 100 for display** |

## Classification Thresholds

| Score (normalised) | Classification | Recommended Action |
|---|---|---|
| 70–100 | MATCH | Log to pipeline; trigger Bid/No-Bid review |
| 40–69 | MAYBE | Log to pipeline; lower priority |
| 0–39 | IGNORE | Do not log |
| DISQUALIFIED | DISQUALIFIED | Do not log; audit trail only |

## Mandatory Disqualification Gates (applied before scoring)

These gates override the score entirely. A single gate trigger = DISQUALIFIED regardless of fit.

1. **Missing mandatory certification** — SSIP (CHAS, SafeContractor, Constructionline Gold, or Achilles Building Confidence), ISO 9001, or any other credential explicitly required by the notice and not held by the company. Note: Under the Procurement Act 2023, the Central Digital Platform (formerly Selection Questionnaire) supplier information regime replaces PAS 91 — the buyer may specify additional exclusion grounds under Schedule 6 / 7 of the Act.
2. **Exceeds financial capacity ceiling** — Estimated value above the company's declared maximum contract size.
3. **Matches a declared exclusion rule** — e.g., "Exclude all demolition-only contracts" or "Exclude contracts below £250k".
4. **Contract Details Notice** — Under Procurement Act 2023 this is the post-award transparency publication (replacing the OJEU Contract Award Notice). Route to competitor intelligence log; do not treat as a pursuit opportunity.

## Specification Bias Indicators (advisory flags only)

- Proprietary brand or system names in the specification
- Extremely narrow technical requirements matching only one or two known suppliers
- Tender period shorter than 25 working days for a "below-threshold" competitive process, or shorter than the statutory minimum for the chosen route (see Procurement Act 2023 minimum timescales)
- Evaluation criteria weighted >80% on price — under the Procurement Act 2023 the concept of "most advantageous tender" (MAT) replaces MEAT and explicitly permits weightings beyond price/quality, so a heavy-price weighting on a complex works contract is unusual

## UK Construction CPV Codes Reference

The Procurement Act 2023 continues to use the CPV vocabulary (retained from the pre-Brexit regime).

| CPV Code | Sector |
|---|---|
| 45000000 | Construction work (general) |
| 45100000 | Site preparation |
| 45200000 | Building and civil engineering works |
| 45210000 | Building construction |
| 45211000 | Residential construction |
| 45212000 | Commercial / leisure construction |
| 45214000 | Education sector construction |
| 45215000 | Healthcare construction |
| 45216000 | Emergency services / public order buildings |
| 45220000 | Civil engineering |
| 45230000 | Infrastructure (roads, bridges, pipelines) |
| 45231000 | Pipelines and utilities |
| 45232000 | Water and wastewater |
| 45261000 | Roofing and cladding |
| 45300000 | M&E and fit-out |
| 45310000 | Electrical installation |
| 45330000 | Plumbing and drainage |
| 45400000 | Building completion and finishing |
| 45500000 | Plant hire and demolition |

## Tender Alert Sources Monitored

| Source | Notice Types | Frequency | UK Relevance |
|---|---|---|---|
| Find a Tender (FTS) — find-tender.service.gov.uk | Above-threshold Tender Notices, Preliminary Market Engagement Notices, Transparency Notices, Contract Details Notices | Daily digest email + RSS | **Primary** — all above-threshold UK public works post-Brexit (replaces OJEU) |
| Contracts Finder — contractsfinder.service.gov.uk | Below-threshold and above-threshold notices from central government and public bodies | Daily digest + API | **Primary** for below-threshold work |
| Sell2Wales, Public Contracts Scotland, eTendersNI | Devolved-nation portals | Daily digest | Regional coverage — Wales, Scotland, Northern Ireland |

## Procurement Act 2023 — Public Contracts Thresholds (from 1 January 2026)

Thresholds are updated biennially by SI; values below are inclusive of VAT for goods/services and exclusive for works (per the Act's convention).

| Contract Type | Threshold |
|---|---|
| Works contracts | £5,372,609 (approx — check current SI) |
| Goods and services (central government) | £139,688 |
| Goods and services (sub-central authorities) | £214,904 |
| Light-touch regime (services listed in Schedule 1) | £663,540 |

Contracts above these thresholds must be advertised on Find a Tender. Below-threshold public contracts of £30,000+ must still be advertised on Contracts Finder under the transparency regime.

## Procurement Act 2023 — Recognised Notice Types

The Act introduces a more prescribed notice regime. The Opportunity Monitor should recognise:

- **Pipeline Notice** — annual look-ahead of contracts over £2m (contracting authorities with spend > £100m)
- **Preliminary Market Engagement Notice (PMEN)** — pre-market engagement; strategic value equivalent to a PIN
- **Tender Notice** — the primary live-opportunity notice
- **Transparency Notice** — used for direct awards
- **Contract Award Notice** — pre-award of intention to award
- **Contract Details Notice** — post-award publication of contract terms
- **Contract Performance Notice** — KPI publication during delivery
- **Contract Termination Notice**

## UK Bid Cadence Alignment

| Stage | UK equivalent | Opportunity Monitor Role |
|---|---|---|
| Strategic need | Pipeline Notice, Preliminary Market Engagement Notice | Flag PMENs scoring ≥70 for pre-market engagement |
| Pre-tender engagement | Buyer runs PME under Procurement Act 2023 s.16–17 | Draft engagement brief; flag CRP/Social Value likely weightings |
| Live tender | Tender Notice | Route to Bid/No-Bid |
| Award | Contract Award Notice → Contract Details Notice | Log to Competitor Intelligence |
