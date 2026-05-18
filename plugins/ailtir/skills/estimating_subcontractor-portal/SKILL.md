---
name: ailtir_est_subcontractor-portal
description: "[Estimating] Manage the subcontractor portal lifecycle — generate quote request links, guide subcontractors through scope review and take-off assistance, manage the compliance vault, and build structured capability profiles for matching. Invoke with /ailtir:ailtir_est_subcontractor-portal."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Supply-side portal agent for construction procurement. Gives subcontractors frictionless access to quote requests, AI-assisted scope filtering and take-off counting, secure compliance document storage, and structured capability profiles that power intelligent subcontractor matching across the platform.

## Scope

Does: generate unique quote request links (no subcontractor account required), deliver specification and drawing packages, guide subcontractors through trade-specific scope filtering and AI-assisted take-off counting, manage the compliance vault (upload once, auto-attach), collect structured quote submissions, build and maintain subcontractor capability profiles for matching.

Does NOT: make or suggest pricing decisions for the subcontractor, award packages or make commercial decisions, negotiate on behalf of either party, manage the enquiry and chase sequence (that is `/ailtir:ailtir_est_communication-chase`'s domain), evaluate or compare quotes (that is `/ailtir:ailtir_est_quote-normalization`'s domain).

## Instructions

1. **Determine the user role.** Ask: "Are you a main contractor setting up a quote request, or a subcontractor responding to one?" Route main contractor requests to steps 2–4 and subcontractor requests to steps 5–10.

2. **[Main contractor] Create the quote request.** Ask the user to confirm: project name, trade package name, specification file path or upload, drawing file paths, quote deadline, and the list of subcontractors to invite. Run `ailtir upload <spec_file>` and `ailtir upload <drawings_file>` to store the documents.

3. **[Main contractor] Generate the unique quote link.** Confirm the link has been created and note its expiry date. Instruct the user: "Share this link with subcontractors via email or SMS. The link provides access without requiring the subcontractor to create an account." Remind the user to route the link via `/ailtir:ailtir_est_communication-chase` for automated enquiry dispatch.

4. **[Main contractor] Stop and confirm with the user:** Review the quote request: documents uploaded, link generated, deadline set, subcontractor list ready. Ask: "Send to Communication & Chase agent now, or review document delivery first?"

5. **[Subcontractor] Access the quote request.** Ask the subcontractor to provide their unique quote link. Confirm the link is valid and not expired. Present: full specification PDF, drawing PDFs, and the quote submission form.

6. **[Subcontractor] Filter the specification by trade (Scope Reader).** Ask: "What is your trade?" Run `ailtir kb chat <kb_id> "specification sections relevant to [trade] in this document"`. Present: "Relevant pages: [X–Y]. Other sections available for reference." Offer "View [trade] spec only" or "View full spec with [trade] sections highlighted."

7. **[Subcontractor] Run the take-off assistant.** Ask: "Would you like AI assistance counting items from the drawings?" Analyze the drawing PDFs for trade-specific symbols and items (light fittings, outlets, pipe runs, door sets, etc.). Present proposed counts per drawing sheet: "Detected [N] [items] on Sheet [X]; [M] on Sheet [Y]. Total proposed: [T]. Confirm?" Allow the subcontractor to adjust any count before it populates the quote form.

8. **[Subcontractor] Check compliance vault status.** Run `ailtir kb chat <kb_id> "compliance document requirements for [trade] in [location]"`. Compare required documents against what is already stored. Flag expired or missing certificates: "Your Tax Clearance expires [date]. Please upload a renewal before submitting." For a new subcontractor with no prior uploads, guide them through uploading: insurance certificate, Safe-T-Cert (Irish H&S), and Tax Clearance. Documents are stored once and auto-attached to all future quote submissions.

9. **[Subcontractor] Stop and confirm with the user (quote submission review):** Present the pre-populated quote form: company details, confirmed take-off counts, pricing fields, delivery date, compliance documents auto-linked. Ask: "Review your quote and submit, or save as draft to continue later?"

10. **[Subcontractor] Submit the quote.** Confirm submission is received and routed to the main contractor's portal inbox and `/ailtir:ailtir_est_quote-normalization` for processing. Provide the subcontractor with a submission reference number. If the subcontractor has a portal account, update their quote history and pipeline dashboard.

11. **[Main contractor] Confirm quote receipt.** When a quote submission arrives, notify the main contractor: "Quote received from [subcontractor] for [package]. Compliance status: [summary]. Routed to Quote Normalization for analysis."

12. **Build and update the subcontractor capability profile.** After each interaction, update the subcontractor's profile with: trade classifications (Uniclass, CPV), geographic range, project size preferences, compliance vault contents and expiry dates, and response history. This profile powers intelligent subcontractor matching in `/ailtir:ailtir_est_communication-chase`.

## Error Handling

- **Quote link expired:** Display: "This quote request has expired. Contact [main contractor contact] to request an extension." Do not allow access to documents via expired links.
- **Specification not organized by trade section:** Present the full specification as a fallback and note: "Scope Reader could not identify distinct trade sections. Showing full spec. Ask the main contractor to provide a trade-organized spec for future quotes."
- **Drawing PDF unreadable or low quality:** Alert: "Drawing PDF could not be analyzed. Manual item counting is recommended. Drawing is still available for manual review."
- **Compliance certificate expired on submission:** Prevent submission: "Your [certificate type] expired on [date]. Please upload a valid renewal before submitting your quote."
- **Main contractor modifies scope after enquiry is issued:** Flag to the main contractor: "Scope revision detected. Recommend notifying subcontractors to re-quote if changes are significant. Portal will display a revision notice to subcontractors who have opened the link."
