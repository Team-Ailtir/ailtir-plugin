---
name: tender-upload
description: Upload a ZIP archive of tender documents to Ailtir. Invoke with /ailtir:tender-upload or /ailtir:tender-upload /absolute/path/to/tender.zip. If no path is provided, browse the filesystem to locate the ZIP file.
argument-hint: "[/absolute/path/to/tender.zip]"
allowed-tools: Bash mcp__filesystem__list_directory mcp__filesystem__read_file
---

Upload a tender ZIP archive to the Ailtir platform using the `ailtir` CLI.

## Instructions

1. **If `$ARGUMENTS` is provided** and ends in `.zip`, treat it as the absolute path
   to the ZIP file. Skip to step 3.

2. **If no argument is given**, use the `filesystem` MCP server to help the user
   locate their ZIP file:
   - Start by listing `~/Downloads` and `~/Documents`
   - Ask the user to confirm or suggest a different location if not found
   - Resolve the chosen path to an absolute path

3. **Confirm** the chosen file path with the user before uploading.

4. **Run the upload:**

   ```bash
   ailtir upload <absolute-path-to-zip>
   ```

5. **On success**, report the `kb_id` from the CLI output. Remind the user they can
   run `ailtir analyse <kb_id>` next to build their knowledge base.

6. **On failure**, show the error and suggest:
   - Checking that `AILTIR_CLI_API_TOKEN` is set (run `echo $AILTIR_CLI_API_TOKEN`)
   - Confirming the file exists and is a valid ZIP archive
   - Running `ailtir version` to verify the CLI is installed
