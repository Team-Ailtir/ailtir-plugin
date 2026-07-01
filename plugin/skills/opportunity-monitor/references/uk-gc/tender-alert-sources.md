# UK Construction Tender Alert Sources

## Primary Sources (Daily Email Alerts and Feeds)

### Find a Tender Service (FTS) — find-tender.service.gov.uk
The official UK government procurement portal for above-threshold notices under the Procurement Act 2023. Replaced OJEU/TED for UK public procurement from 1 January 2021 (post-Brexit) and is now the primary publication venue under the Procurement Act 2023 (in force 24 February 2025).

**Coverage:** All above-threshold notices from UK contracting authorities across central government, local authorities, NHS, education, and utilities.

**Registration:** Suppliers register at find-tender.service.gov.uk and configure CPV code and location filters. FTS supports both **daily email digests** and an **Atom/RSS feed** (`/api/1.0/ocds/search.atom`) — prefer the RSS/API path for scripted ingestion where the Ailtir workspace supports it.

**Key CPV Codes for General Contractors:**
| CPV Code | Description |
|---|---|
| 45000000 | Construction work |
| 45200000 | Works for complete or part construction and civil engineering work |
| 45210000 | Building construction work |
| 45211000 | Construction work for multi-dwelling buildings and individual houses |
| 45214000 | Construction work for buildings relating to education and research |
| 45215000 | Construction work for buildings relating to health and social services |
| 45216000 | Construction work for buildings used by the military or police forces |
| 45220000 | Engineering works and construction works |
| 45230000 | Construction work for pipelines, communication and power lines, for highways, roads, airfields and railways |
| 45260000 | Roof works and other special trade construction works |
| 45300000 | Building installation work |
| 45400000 | Building completion work |

**Email format:** FTS digests arrive from `no-reply@find-tender.service.gov.uk` and list each new notice with title, contracting authority, notice type (Tender Notice / PMEN / Contract Details Notice etc.), publication date, and a link to the notice.

### Contracts Finder — contractsfinder.service.gov.uk
The primary portal for **below-threshold** UK central government contracts (≥£12,000 for central government, ≥£30,000 for sub-central). Also carries some above-threshold notices which are duplicated to FTS.

**Registration:** contractsfinder.service.gov.uk — supports keyword and CPV filtering with daily email alerts and a public JSON API.

### Devolved-nation portals
| Portal | Coverage | URL |
|---|---|---|
| Sell2Wales | Welsh public sector | sell2wales.gov.wales |
| Public Contracts Scotland (PCS) | Scottish public sector | publiccontractsscotland.gov.uk |
| eTendersNI | Northern Ireland public sector | etendersni.gov.uk |

### Constructionline
A pre-qualification and opportunity-notification service used by many UK contracting authorities to shortlist bidders. Gold and Platinum tiers are frequently mandatory selection criteria under the Procurement Act 2023 supplier information regime.

**Website:** constructionline.co.uk

### Building — Barbour ABI — Glenigan
Subscription market-intelligence services that monitor planning applications, PMENs, and early-stage projects before they reach FTS. Useful for identifying projects 6–18 months ahead of tender.

## Email Parsing Rules

When parsing a daily FTS digest, the email typically follows this format:

```
Subject: Find a Tender: Your saved searches — [Date]

New notices matching your saved searches:

1. [Notice Title]
   Contracting Authority: [Authority Name]
   Notice Type: [Tender Notice / Preliminary Market Engagement Notice / etc.]
   CPV: [Primary CPV code + description]
   Estimated Value: £[value] (excl. VAT)
   Deadline: [DD/MM/YYYY HH:MM]
   Link: https://www.find-tender.service.gov.uk/Notice/...

2. [Notice Title]
   ...
```

The parser should extract: Title, Authority, Notice Type, Estimated Value, Deadline, CPV, and Link for each item. Notice Type is critical — Tender Notice, PMEN, Transparency Notice, and Contract Details Notice each route differently in the scoring model.

## Post-Brexit Note

The UK ceased publishing to TED (Tenders Electronic Daily) on 31 December 2020. Northern Ireland-only procurement continues to be visible on eTendersNI. Historical OJEU references in pre-2021 UK contracts remain valid contractually but should be substituted with FTS references in any new template.
