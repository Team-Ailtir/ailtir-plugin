---
name: kb-list
description: List all Ailtir knowledge bases in your account, showing name, kb_id, and status. Invoke with /ailtir:kb-list.
argument-hint: ""
allowed-tools: Bash
---

List all knowledge bases in the Ailtir account using the `ailtir` CLI.

## Instructions

1. **Run:**

   ```bash
   ailtir list
   ```

2. **On success**, display the output (name, `kb_id`, status) in a readable table.
   If any knowledge bases have status `ready`, remind the user they can chat with
   them using `/ailtir:kb-chat <kb_id>`.

3. **On failure**, show the error and suggest:
   - Checking that `AILTIR_CLI_SECRET` is set (run `echo $AILTIR_CLI_SECRET`)
   - Running `ailtir version` to verify the CLI is installed
