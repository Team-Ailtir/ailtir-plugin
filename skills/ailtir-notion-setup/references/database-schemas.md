# Notion Database Schemas

Use these property definitions when calling `notion-create-database`.

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
- **Value (€):** Number (Format: Euro)
- **Tender Return Date:** Date
- **Procurement Route:** Select (CWMF Restricted, CWMF Open, Private Negotiated, Private D&B, Framework)
- **Win Probability (%):** Number (Format: Percent)
- **Go/No-Go Score:** Number
- **Folder Link:** URL (Link to local/SharePoint folder)

## 3. Subcontractor Directory
- **Company Name:** Title
- **Trade:** Multi-Select (Groundworks, Concrete, Steel, M&E, Carpentry, Partitions, Roofing, Facades, Painting, Landscaping)
- **Status:** Select (Approved, Pending Review, Do Not Use)
- **CIRI Registered:** Checkbox
- **Safe-T-Cert:** Checkbox
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
