---
name: ailtir_compliance-matrix
description: Extracts all ITT requirements into a tracked deliverables matrix. Triggered by /ailtir-cowork-plugin:ailtir_compliance-matrix or when bid-planner runs.
---

# Ailtir Compliance Matrix Builder

You are extracting the exact submission requirements from a tender pack.

## Step 1 — Extract Requirements
Scan the ITT (Instruction to Tenderers) and any Returnable Schedules.
Extract:
- Every evaluation criterion and its weighting.
- Every mandatory returnable document (e.g., Form of Tender, Pricing Schedule, Programme).
- Page limits, formatting rules, and submission methods (e.g., eTenders portal under `ireland-gc`; Find a Tender, Contracts Finder, or the buyer's e-tendering platform such as Delta / Jaggaer / Proactis / In-tend under `uk-gc`).

## Step 2 — Check Templates
Check if the required templates were actually provided in the tender pack. If the ITT says "Complete Schedule 3" but Schedule 3 is missing, flag this as a critical gap.

## Step 3 — Generate Workbook

Assemble a JSON payload from Steps 1–2 and write it to a temp file (e.g. `/tmp/compliance_data.json`). Then call the bundled script:

```
python3 <skill_dir>/scripts/create_compliance_matrix.py \
  --output "Bids/[BidRef]/4-Compliance/Compliance_Matrix_[Project].xlsx" \
  --project "[Name]" \
  --client "[Client]" \
  --data /tmp/compliance_data.json
```

**DATA CONTRACT:**

```json
{
  "tabs": {
    "returnables": {
      "headers": ["Ref", "Requirement / Criterion", "Weighting", "Template Provided", "Owner", "Notes"],
      "rows": [["C1", "Method Statement", "20%", "Yes — Schedule 3", "Bid Manager", ""]]
    },
    "submission_rules": {
      "headers": ["Item", "Requirement", "Notes"],
      "rows": [["Format", "PDF via eTenders portal", "Max 50MB"]]
    },
    "gaps": {
      "headers": ["Ref", "Gap / Query", "Severity", "Action", "Status"],
      "rows": [["G1", "Schedule 3 template missing from pack", "Critical", "RFI to client", "Open"]]
    }
  },
  "optional_tabs": []
}
```

You choose the headers for each tab — use whatever columns best represent the data. Present a summary of findings to the user after generating the workbook.

- [HUMAN INPUT REQUIRED] If the submission method or deadline is not stated in the ITT, ask the user before finalising the matrix.

---

## On Completion — Update Bid State

```
python3 <ailtir_conductor_dir>/scripts/update_frontmatter.py \
    --bid-path Bids/<BID> --complete ailtir_compliance-matrix --result proceed
```

## Anti-Patterns (What NOT to do)
- DO NOT miss mandatory returnables. Scan the entire ITT.
- DO NOT hallucinate deadlines or weightings. Use exact figures from the ITT.
- DO NOT guess the submission method if it is not stated; flag it as a question.

## Quality Checks
- [ ] Every evaluation criterion captured with exact weighting.
- [ ] Missing templates explicitly flagged.
- [ ] Submission method and deadline captured.
