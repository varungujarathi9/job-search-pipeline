# Submission

`/jsp-apply` uses browser automation to open a posting's application page and pre-fill it from a verified tailored draft (see [docs/tailoring.md](tailoring.md)). It never submits.

## Why this is safe by construction

- The command's instructions name the exact submit-labeled controls it must never click, and tell the agent to stop and ask rather than guess when a control's purpose is unclear.
- There is no "auto-submit" mode, flag, or argument - the command has exactly one path, and it ends at "stop" after filling the form.
- The command requires a verified draft (`/jsp-tailor` must have already passed `pipeline/cli/tailor_verify.py`) before it will pre-fill anything.

## What the user does

After `/jsp-apply` stops, the form is filled and the browser tab is left open. The user reviews every field - this is expected to take about two minutes - and clicks submit themselves. Nothing in this repository can do that final click for them.
