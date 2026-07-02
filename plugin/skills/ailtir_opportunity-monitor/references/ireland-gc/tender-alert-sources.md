# Irish Construction Tender Alert Sources

## Primary Sources (Daily Email Alerts)

### eTenders Ireland (etenders.gov.ie)
The official Irish government procurement portal. All public sector contracts above €25,000 must be published here. Contractors register their CPV codes and receive a **daily end-of-day email digest** listing all new tenders matching those codes.

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

**Email format:** The eTenders digest arrives from `etenders@eu-supply.com` and lists each new tender with a title, contracting authority, and a link to the notice.

### OJEU / TED (ted.europa.eu)
Above-threshold contracts (typically €5.35M+ for works) must also be published in the Official Journal of the EU. TED (Tenders Electronic Daily) provides daily email alerts.

**Registration:** ted.europa.eu/TED/misc/chooseSubscribeUser.do

### Construction Information Services (CIS)
A subscription service that monitors planning applications and converts them into early-stage project leads before they reach tender stage. Useful for identifying projects 12-18 months before they go to tender.

**Website:** cis.ie

### Local Authority Procurement Portals
Some local authorities use their own portals or post directly on eTenders. Key ones to monitor:
- Dublin City Council
- Cork City/County Council
- Galway City/County Council

## Email Parsing Rules

When parsing a daily eTenders digest, the email typically follows this format:
```
Subject: eTenders Daily Alert - [Date]

New Tenders Published Today:

1. [Project Title]
   Authority: [Contracting Authority]
   Category: [CPV Description]
   Deadline: [DD/MM/YYYY]
   Link: https://www.etenders.gov.ie/...

2. [Project Title]
   ...
```

The parser should extract: Title, Authority, Deadline, and Link for each item.
