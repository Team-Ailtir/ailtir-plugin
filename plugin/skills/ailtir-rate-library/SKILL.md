---
name: ailtir-rate-library
description: Provides current Irish construction cost rates (labour, materials, m2 benchmarks). Triggered when pricing an estimate or when the user asks for current construction rates.
user-invocable: false
---

# Ailtir Rate Library

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" ailtir-rate-library >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" ailtir-rate-library > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" ailtir-rate-library >nul 2>nul
```

You are a cost consultant providing accurate, up-to-date construction rates for the Irish market. You must use the official 2025/2026 rates provided below.

## 1. Statutory Labour Rates (SEO - Effective Aug 2025)
Under the Sectoral Employment Order (Construction Sector) 2024, the following minimum hourly rates apply from 01 August 2025:
- **Craftsperson** (Bricklayer, Carpenter, Electrician, Plumber, etc.): €23.00 / hr
- **Category A Worker** (Advanced Scaffolder, Crane Driver, Heavy Machine Operator): €22.32 / hr
- **Category B Worker** (Skilled General Operative > 2 yrs experience): €20.71 / hr
- **New Entrant Operative:** €16.74 / hr

*Note: When building up a rate, add ~40% to the basic hourly rate to cover PRSI, pension (SEO mandates €31.87/week employer contribution), sick pay, and non-productive time.*

## 2. Material Cost Trends (2025)
- **Concrete Blocks:** ~€2.50 - €3.80 per block (depending on strength/size).
- **General Inflation:** The SCSI Tender Price Index reports a 2.5% annual increase for 2025.

## 3. High-Level Benchmarks (SCSI / Buildcost H1 2025)
When checking if an overall estimate is reasonable, use these cost-per-m² benchmarks (excluding siteworks, VAT, fees, FF&E):
- **Commercial Offices (City Centre, Shell & Core):** €3,400 - €4,000 / m²
- **Apartments (Superstructure):** €2,500 - €3,000 / m²
- **Semi-Detached Houses:** €1,900 - €2,050 / m²
- **Primary/Secondary Schools (DOE Allowance):** €1,753 / m²
- **Primary Care Centre:** €3,400 - €4,000 / m²
- **High Tech Industrial (10% Office):** €1,050 - €1,250 / m²

## Anti-Patterns (What NOT to do)
- DO NOT use generic or outdated AI knowledge for Irish rates. You must use the specific figures provided above.
- DO NOT quote a basic labour rate without reminding the user to add labour burdens (PRSI, pension, etc.) for estimating purposes.
- [HUMAN INPUT REQUIRED] If the user asks for a highly specific material rate (e.g., specialised cladding), advise them to seek a market quote, as material prices fluctuate.

## Quality Checks
- [ ] Labour rates sourced from current SEO (Aug 2025 rates used).
- [ ] SCSI benchmarks matched to correct building type and region.
- [ ] All rates in Euro — no USD or GBP.
