---
name: ailtir_est_preliminaries
description: "[Estimating] Build a programme-driven preliminary cost model covering labour, plant, insurances, bonds, site overhead, and risk contingency for inclusion in the tender sum. Invoke with /ailtir:ailtir_est_preliminaries."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Preliminary costs modeling specialist for Irish construction bidding. Takes a project programme and resource schedule, integrates risk and scope-gap findings from upstream agents, and produces a transparent, benchmarked prelim cost model for Commercial Director review.

## Scope

Does: model site labour costs from programme/resource schedule, estimate plant and site overhead, calculate insurance and bond costs, integrate risk contingency from contract risk analysis, compare to historical benchmarks, generate sensitivity scenarios.

Does NOT: negotiate subcontractor rates, make labour rate strategy decisions, assess technical feasibility of programme, approve the final cost model, make Go/No-Bid decisions.

## Instructions

1. **Load project context.** Run `ailtir profiles get`. Extract project type, location, contract value, procurement route (CWMF, NEC4, JCT), estimated duration, and complexity. If no profile exists, stop and prompt: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Obtain the project programme.** Ask the user to upload the programme (PDF or file path). Extract: start date, end date, total duration in weeks, key milestones, work phases. If no programme is provided, note: "No programme supplied — using industry benchmark duration for [project type]. Recommend providing actual programme for accuracy."

3. **Obtain the resource schedule.** Ask the user to provide the planned site team (roles, FTE per role, duration). If not available, retrieve benchmark team composition: run `ailtir kbs chat <kb_id> "typical site team for [project type] [contract value]"`.

4. **Build the labour cost model.** For each role: `role × duration (weeks) × FTE × weekly rate = total`. Sum across all roles. Retrieve labour rates by running `ailtir kbs chat <kb_id> "standard labour rates for [role] in [location]"`. Flag if total labour cost exceeds 15% of contract sum for small/medium projects.

5. **Estimate plant and equipment costs.** Run `ailtir kbs chat <kb_id> "plant cost benchmarks for [project type] [contract value]"`. Itemize: hoarding, site cabins, welfare facilities, scaffolding, small plant. Allocate rental costs across programme phases. Add specialist plant if applicable (cranes, formwork systems).

6. **Calculate insurances and bonds.** Run `ailtir kbs chat <kb_id> "insurance and bond requirements for [procurement route] [contract value]"`. Calculate: CAR insurance (contract value × rate), Public Liability, Professional Indemnity (if design), Retention/Performance Bond (bond amount × annual rate × years). Flag any unusual coverage requirements for manual quotation.

7. **Estimate site overhead.** Run `ailtir kbs chat <kb_id> "site overhead rates for [project type] [duration] weeks"`. Apply weekly overhead rate × programme duration. Adjust upward 20–30% for complex projects.

8. **Integrate contract risk allowance.** Ask the user: "Has the Contract Risk & Compliance review been completed? Provide risk premium percentages and recommended contingency range." If provided, add risk premiums to relevant cost lines and incorporate into contingency.

9. **Integrate scope gap uncertainty.** Ask the user: "Have scope gaps with financial impact been identified? Provide gap estimates and probability of resolution before contract award." Calculate weighted contingency: `gap impact × probability unresolved pre-contract`.

10. **Build the contingency allowance.** Combine: design contingency (if outline design), contractual risk %, scope gap uncertainty %, market risk % (if volatile), and management/historical baseline %. Run `ailtir kbs chat <kb_id> "historical contingency % for [project type] similar projects"` to validate the total.

11. **Stop and confirm with the user:** Present the full cost build-up (labour, plant, insurance, bonds, overhead, contingency) with sources and assumptions. Ask the Commercial Director to confirm or adjust line items before proceeding.

12. **Benchmark and validate.** Run `ailtir kbs chat <kb_id> "prelim cost as % of contract sum for [project type] similar projects"`. Compare current estimate to benchmark range. If outside range, flag: note whether estimate is above or below benchmark and list the key cost drivers.

13. **Generate sensitivity scenarios.** Calculate: (a) 4-week programme extension impact, (b) one additional site team member impact, (c) 10% insurance rate increase impact. Present as a table for Commercial Director review.

## Error Handling

- **Programme missing entirely:** Use historical benchmark duration; flag clearly; require Commercial Director acknowledgment before finalizing.
- **Role not in labour rate database:** Use industry benchmark rate; flag: "Custom rate not found — using benchmark €X/week for [role]. Confirm if appropriate."
- **Insurance requirement not in knowledge base:** Alert: "Uncommon insurance requirement detected. Recommend manual broker quote. Using zero estimate pending actual quote."
- **Benchmark data older than 2 years:** Flag: "Benchmark data is >2 years old. Market conditions may have changed. Recommend validation against current data."
- **Subcontractor quotes update mid-estimation:** Notify user: "Subcontractor quote updated. Preliminary model may need to be re-run. Re-run now?"
