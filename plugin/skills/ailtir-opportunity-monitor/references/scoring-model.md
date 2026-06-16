# Ailtir Opportunity Scoring Model

This reference file defines the 5-dimension strategic fit scoring model used by the Opportunity Monitor. The model is derived from the Ailtir Agent PRD (Agent 2.1 — Opportunity Intelligence).

## Scoring Dimensions

| Dimension | Max Points | Description |
|---|---|---|
| Sector Match | 25 | CPV code alignment with company's declared sector focus |
| Geographic Preference | 20 | Location of works vs. company's preferred regions |
| Contract Value Fit | 20 | Estimated value vs. company's sweet spot range |
| Procurement Route | 15 | Route type vs. company's preferred procurement routes |
| Notice Type Bonus | 10 | Live Contract Notice or strategic PIN |
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

1. **Missing mandatory certification** — CIRI registration, Safe-T-Cert, ISO 9001, or other explicitly required credential not held by the company.
2. **Exceeds financial capacity ceiling** — Estimated value above the company's declared maximum contract size.
3. **Matches a declared exclusion rule** — e.g., "Exclude all demolition-only contracts" or "Exclude contracts below €250k".
4. **Contract Award Notice** — Not a pursuit opportunity; route to competitor intelligence log instead.

## Specification Bias Indicators (advisory flags only)

The following signals suggest the specification may be written around an incumbent. Flag but do not disqualify.

- Proprietary brand or system names in the specification
- Extremely narrow technical requirements matching only one or two known suppliers
- Tender period shorter than 10 working days for a complex contract (CWMF minimum is typically 15–25 working days)
- Evaluation criteria weighted >80% on price (unusual for public works; may indicate pre-determined outcome)

## Irish Construction CPV Codes Reference

The following CPV codes are the primary codes for Irish construction procurement. Use these to assess sector match.

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

| Source | Notice Types | Frequency | Irish Relevance |
|---|---|---|---|
| eTenders.gov.ie | Contract Notices, PINs, Award Notices | Daily digest email | **Primary** — all Irish public procurement |
| TED (ted.europa.eu) | OJEU Contract Notices (above EU thresholds) | Daily digest email | High — all above-threshold Irish public works |
| Find a Tender (UK) | UK Contract Notices | Daily digest email | Relevant for cross-border NI/UK work |
| eTendersNI | NI Contract Notices | Daily digest email | Relevant for NI work |

## EU Procurement Thresholds (2024–2025)

| Contract Type | Threshold (excl. VAT) |
|---|---|
| Works contracts (public authorities) | €5,538,000 |
| Works contracts (utilities) | €5,538,000 |
| Services / Supplies (central government) | €143,000 |
| Services / Supplies (other public bodies) | €221,000 |

Contracts above these thresholds must be published on TED (OJEU) in addition to eTenders.

## CWMF Gate Alignment

The Opportunity Monitor feeds into the CWMF Gate Review process as follows:

| Gate | Stage | Opportunity Monitor Role |
|---|---|---|
| Gate 0 | Strategic need identified | PIN monitoring — flag pre-market engagement window |
| Gate 1 | Preliminary design / business case | Pre-Market Engagement Brief for PINs scoring ≥70 |
| Gate 2 | Detailed design | Contract Notice published — route to Bid/No-Bid |
| Gate 3 | Tender | Bid/No-Bid decision made; bid team activated |
