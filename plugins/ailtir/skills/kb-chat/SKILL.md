---
name: kb-chat
description: Ask a natural-language question against an Ailtir knowledge base. Invoke with /ailtir:kb-chat <kb_id> <question>. Sends the last 5 conversation interactions as context alongside the question.
argument-hint: "<kb_id> <question>"
allowed-tools: Bash
---

Ask a question against an Ailtir knowledge base using the `ailtir` CLI, enriched
with recent conversation context.

## Instructions

1. **Parse `$ARGUMENTS`**: the first whitespace-delimited token is the `kb_id`;
   everything after it is the `question`.

2. **If either is missing**, ask the user to provide both the `kb_id` and the
   question before proceeding. Offer to run `/ailtir:kb-list` to find a valid `kb_id`.

3. **Build context** from the last 5 conversation interactions (each interaction
   is one user message plus the assistant reply that followed it). Format them as:

   ```
   Here is the question: <question>

   Here is more context to answer the question:
   - Q: <user message N-4> A: <assistant reply N-4>
   - Q: <user message N-3> A: <assistant reply N-3>
   - Q: <user message N-2> A: <assistant reply N-2>
   - Q: <user message N-1> A: <assistant reply N-1>
   - Q: <user message N>   A: <assistant reply N>
   ```

   Omit interactions that are not relevant (e.g. skill invocations, file uploads).
   If fewer than 5 interactions exist, include only what is available.

4. **Run the query:**

   ```bash
   ailtir chat <kb_id> "<enriched question with context>"
   ```

5. **On success**, present the CLI response clearly to the user.

6. **On failure**, show the error and suggest:
   - Checking that `AILTIR_CLI_SECRET` is set (run `echo $AILTIR_CLI_SECRET`)
   - Confirming the `kb_id` is correct and its status is `ready` (run `ailtir list`)
   - Running `ailtir version` to verify the CLI is installed
