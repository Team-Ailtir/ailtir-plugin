---
name: ailtir_kb_analyse
description: Trigger the Ailtir ingestion pipeline for a knowledge base. Invoke with /ailtir:ailtir_kb_analyse or /ailtir:ailtir_kb_analyse <kb_id>. If no kb_id is provided, run ailtir kbs list to let the user pick one.
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Trigger the ingestion pipeline for an Ailtir knowledge base using the `ailtir` CLI.

## Instructions

1. **If `$ARGUMENTS` is provided**, treat it as the `kb_id`. Skip to step 3.

2. **If no argument is given**, run `ailtir kbs list` and show the output to the user.
   Ask them to confirm which `kb_id` to analyse.

3. **Confirm** the `kb_id` with the user before proceeding.

4. **Run the ingestion:**

   ```bash
   ailtir kbs analyse <kb_id>
   ```

5. **On success**, inform the user that ingestion has been triggered and that it
   takes a few minutes. Suggest running `ailtir kbs list` to check status, or using
   `/ailtir:ailtir_kb_list` to do so from here.

6. **On failure**, show the error and suggest:
   - Checking that `AILTIR_CLI_API_TOKEN` is set (run `echo $AILTIR_CLI_API_TOKEN`)
   - Confirming the `kb_id` is correct by running `ailtir kbs list`
   - Running `ailtir version` to verify the CLI is installed
