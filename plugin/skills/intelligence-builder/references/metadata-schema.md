# Ailtir Intelligence Metadata Schema

Every Markdown file saved to the `Intelligence/` folder MUST begin with a YAML frontmatter block. This allows Claude to filter and select relevant intelligence at near-zero token cost without reading the full file contents.

The enums below are supersets across both `ireland-gc` and `uk-gc` profiles — use the value that applies to the source project. When you add a new intelligence entry, tag it with the `profile_key` field so downstream filtering can distinguish Irish from UK material where relevant.

Use the exact schemas below based on the document type.

## 1. Case Studies (`Intelligence/case-studies/`)
```yaml
---
type: case-study
title: "[Project Name]"
client: "[Client Name]"
profile_key: [ireland-gc | uk-gc]
sector: [Education, Public Works, Commercial, Residential, Healthcare, Infrastructure, etc.]
procurement_route: [CWMF-Restricted, CWMF-Open, Private-Negotiated, Private-D&B, Framework, Open-Procedure, Competitive-Flexible-Procedure, Framework-Call-Off, Dynamic-Market]
value: [Number, e.g. 2400000]
value_currency: [EUR | GBP]
duration_weeks: [Number]
location: "[County / Region / Devolved-Nation]"
completion_date: YYYY-MM
outcome: [Won | Lost | Ongoing]
key_themes: [List of key themes, e.g. Phased-Construction, Occupied-Building, BREEAM, Net-Zero, Building-Safety-Act]
accreditations_used: [List, e.g. CIRI, Safe-T-Cert, SSIP-CHAS, SSIP-SafeContractor, Constructionline-Gold, ISO-9001, ISO-14001, ISO-45001, BSA-Principal-Contractor]
evaluator_score: [Number 0-100, if known from feedback]
use_for: [PQQ, Quality-Submission, Post-Tender-Interview]
---
```

## 2. Method Statements (`Intelligence/method-statements/`)
```yaml
---
type: method-statement
title: "[Task Name]"
task: "[Specific Task, e.g. Temporary-Propping, Deep-Excavation, Traffic-Management]"
profile_key: [ireland-gc | uk-gc | any]
sector: [Any, or specific sectors]
contract_type: [PW-CF1, PW-CF5, RIAI, JCT-SBC, JCT-DB, NEC4-ECC-A, NEC4-ECC-C, FIDIC-Red, FIDIC-Yellow, Bespoke, Any]
complexity: [Low | Medium | High]
last_used: YYYY-MM
approved_by: "[Name and Role]"
status: [Draft | Approved | Superseded]
use_for: [Quality-Submission, Contract-Admin, Site-Diary]
---
```

## 3. Win Themes (`Intelligence/win-themes/`)
```yaml
---
type: win-theme
theme: "[Theme Title, e.g. CIRI-Registered Supply Chain, SSIP+Constructionline-Gold, Net-Zero-Delivery]"
profile_key: [ireland-gc | uk-gc | any]
sector: [Any, or specific sectors]
procurement_route: [Any, or specific routes]
strength_level: [Primary | Secondary | Supporting]
evidence_files: ["[List of related case study filenames, e.g. case-studies/2024-Ballymun-School.md]"]
use_for: [Quality-Submission, PQQ, Post-Tender-Interview]
---
```

## 4. Rate Library Entries (`Intelligence/rate-library/`)
```yaml
---
type: rate
trade: "[Trade, e.g. Groundworks, Concrete, MEP, Roofing]"
item: "[Description]"
unit: "[m³, m², nr, t, item]"
rate: [Number]
rate_currency: [EUR | GBP]
source: "[e.g. SCSI-2025, Buildcost-2025, BCIS-Q2-2026, Subcontractor-Quote]"
profile_key: [ireland-gc | uk-gc]
region: [Dublin, Leinster, Munster, Connacht, Ulster, London, South-East, South-West, Midlands, North, Scotland, Wales, Northern-Ireland, Any]
last_updated: YYYY-MM
confidence: [High | Medium | Low]  # Low = estimate only
---
```

## 5. Lessons Learned (`Intelligence/lessons-learned/`)
```yaml
---
type: lessons-learned
project: "[Project Name]"
bid_ref: "[YYYY-NNN-ProjectName]"
outcome: [Won | Lost]
score_received: [Number 0-100]
winning_score: [Number 0-100, if known]
key_lessons: [List of short tags, e.g. Insufficient-Quantification, Weak-Programme, Price-Too-High]
action_taken: "[What was changed in the business/intelligence base as a result]"
date: YYYY-MM
---
```
