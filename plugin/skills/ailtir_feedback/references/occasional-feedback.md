# Occasional Feedback Schedule

After the current workflow completes successfully, run the bundled
`scripts/feedback_schedule.py` helper from the `ailtir_feedback` skill with the
`complete` command. Do not run it for a cancelled or failed workflow.

Read the JSON result:

- If `invite` is `false`, finish without mentioning feedback.
- If `invite` is `true`, use `AskUserQuestion` when available to ask whether the
  user would like to provide brief feedback now. Offer exactly `Give feedback`
  and `Not now`. State that the feedback is anonymous, optional, and takes about
  one minute.

After the user answers, run the helper with the `prompted` command so the same
invitation is not repeated. If the user chooses `Give feedback`, invoke the
`ailtir_feedback` skill and follow it completely. If they choose `Not now`,
finish without persuasion or another feedback question.

The helper schedules an invitation after the first successful substantive
workflow, then no more frequently than every 5 completed workflows or 10 days.
It remains disabled until `ailtir_setup` has explained reporting and enabled it.
Never invite feedback from inside the `ailtir_feedback` or `ailtir_setup` skill.
