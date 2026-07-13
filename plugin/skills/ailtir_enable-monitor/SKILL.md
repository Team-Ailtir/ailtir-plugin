---
name: ailtir_enable-monitor
description: Configures the daily automated opportunity monitor. Connects your email and Notion, and schedules the background task to run every morning. Triggered by /ailtir-cowork-plugin:ailtir_enable-monitor.
---

# Enable Opportunity Monitor

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_enable-monitor`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are the Ailtir Setup Assistant. The user wants to enable the automated daily opportunity monitor.

## Step 1: Verify Connectors
Check if the required connectors are active using `manus-config config load`.
1. **Email Connector:** (Gmail or Microsoft 365 Outlook) — Required to read the tender-alert digests. Under `ireland-gc` this is the eTenders digest from `etenders@eu-supply.com`; under `uk-gc` this is the Find a Tender / Contracts Finder digest.
2. **Notion Connector:** Required to log the leads into the Bid Pipeline.

If either is missing, instruct the user to enable them via the Manus interface, and wait for them to confirm before proceeding.

## Step 2: Create the Scheduled Task
Once connectors are verified, create the scheduled task using `manus-config schedule create`.

Run the following command:
```bash
manus-config schedule create \
  --title "Ailtir Opportunity Monitor" \
  --detail "Run the /ailtir-cowork-plugin:ailtir_opportunity-monitor workflow to check my email for the tender-alert digests appropriate to my active Ailtir profile (Irish eTenders/TED under ireland-gc, UK Find a Tender / Contracts Finder under uk-gc), filter them against my company profile, and log matches to my Notion Bid Pipeline." \
  --cron "0 0 8 * * 1-5" \
  --repeated
```
*(This cron string runs the task at 08:00 AM every weekday, Monday through Friday).*

## Step 3: Confirm Setup
Tell the user:
"The Opportunity Monitor is now active. Every weekday morning at 8:00 AM, it will automatically check your email for tender alerts, filter out the noise, and log any strong matches directly into your Notion Bid Pipeline."

## Anti-Patterns (What NOT to do)
- DO NOT attempt to create the schedule if the email connector is not enabled.
- DO NOT set the cron job to run more than once a day. Both eTenders and Find a Tender send at most one digest per day.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
