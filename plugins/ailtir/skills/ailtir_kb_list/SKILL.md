---
name: ailtir_kb_list
description: List all Ailtir knowledge bases in your account, showing name, kb_id, and status. Invoke with /ailtir:ailtir_kb_list.
argument-hint: ""
allowed-tools: Bash
---

List all knowledge bases in the Ailtir account using the `ailtir` CLI.

## Instructions

1. **Run:**

   ```bash
   ailtir kbs list
   ```

2. **On success**, display the output (name, `kb_id`, status) in a readable table.
   If any knowledge bases have status `ready`, remind the user they can chat with
   them using `/ailtir:ailtir_kb_chat <kb_id>`.

3. **On failure**, show the error and suggest:
   - Checking that `AILTIR_CLI_API_TOKEN` is set (run `echo $AILTIR_CLI_API_TOKEN`)
   - Running `ailtir version` to verify the CLI is installed
