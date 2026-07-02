# Notion Database Schemas

Use these property definitions when calling `notion-create-database`. The schemas are a superset across both `ireland-gc` and `uk-gc` profiles — a user on either profile simply leaves the fields they do not need blank. This keeps the Notion cache portable if a company operates in both markets.

## 1. CRM (Clients & Architects)
- **Name:** Title
- **Type:** Select (Client, Architect, PQS, Engineer, Project Manager)
- **Status:** Select (Active, Target, Dormant)
- **Key Contact:** Rich Text
- **Email:** Email
- **Phone:** PhoneNumber
- **Notes:** Rich Text

## 2. Bid Pipeline
- **Project Name:** Title
- **Status:** Status (Pre-Tender, Live, Submitted, Won, Lost, Declined)
- **Client:** Relation (Points to CRM)
- **PQS/Architect:** Relation (Points to CRM)
- **Value:** Number (Format: Euro for `ireland-gc` workspaces, Pound Sterling for `uk-gc` workspaces — set at database-creation time)
- **Tender Return Date:** Date
- **Procurement Route:** Select — combined list covering both profiles: `CWMF Restricted`, `CWMF Open`, `Private Negotiated`, `Private D&B`, `Private Traditional`, `Framework Call-Off`, `Open Procedure` (UK), `Restricted Procedure` (UK, legacy), `Competitive Flexible Procedure` (UK Procurement Act 2023), `Direct Award` (UK Procurement Act 2023), `Dynamic Market` (UK)
- **Notice Type:** Select — combined: `Contract Notice`, `PIN` (Ireland), `Tender Notice` (UK), `PMEN` (UK Preliminary Market Engagement Notice), `Pipeline Notice` (UK), `Transparency Notice` (UK), `Contract Details Notice` (UK)
- **Win Probability (%):** Number (Format: Percent)
- **Go/No-Go Score:** Number
- **Folder Link:** URL (Link to local/SharePoint folder)

## 3. Subcontractor Directory
- **Company Name:** Title
- **Trade:** Multi-Select (Groundworks, Concrete, Steel, M&E, Carpentry, Partitions, Roofing, Facades, Painting, Landscaping)
- **Status:** Select (Approved, Pending Review, Do Not Use)
- **CIRI Registered:** Checkbox (Ireland)
- **Safe-T-Cert:** Checkbox (Ireland)
- **SSIP Held:** Checkbox (UK — umbrella marker; specify scheme below)
- **CHAS:** Checkbox (UK SSIP)
- **SafeContractor:** Checkbox (UK SSIP)
- **Constructionline:** Select (UK — None, Bronze, Silver, Gold, Platinum)
- **ISO 9001:** Checkbox
- **ISO 14001:** Checkbox
- **ISO 45001:** Checkbox
- **Modern Slavery Statement Current:** Checkbox (UK — required if their turnover ≥£36m)
- **Insurance Expiry:** Date
- **Key Contact:** Rich Text
- **Email:** Email
- **Phone:** PhoneNumber
- **Performance Rating:** Select (⭐, ⭐⭐, ⭐⭐⭐, ⭐⭐⭐⭐, ⭐⭐⭐⭐⭐)
- **Notes:** Rich Text

## 4. RFI Log
- **RFI Number:** Title (e.g., RFI-001)
- **Project:** Relation (Points to Bid Pipeline)
- **Question:** Rich Text
- **Status:** Status (Draft, Submitted, Answered, Closed)
- **Date Submitted:** Date
- **Date Answered:** Date
- **Answer:** Rich Text
- **Impact:** Select (Cost, Programme, Scope, None)
