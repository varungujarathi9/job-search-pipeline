# Submission

`/jsp-apply <dedupe_key> [dedupe_key ...]` uses browser automation to open one or more postings' application pages, each in its own tab, and pre-fill each from its verified tailored draft and tailored resume PDF (see [docs/tailoring.md](tailoring.md)). It never submits.

## Why this is safe by construction

- The command's instructions name the exact submit-labeled controls it must never click, and tell the agent to stop and ask rather than guess when a control's purpose is unclear. This holds per application - finishing one form never relaxes the rule for the next.
- There is no "auto-submit" mode, flag, or argument - the command has exactly one path, and it ends at "stop" after filling every form in the run.
- The command requires a verified draft (`/jsp-tailor` must have already passed `pipeline/cli/tailor_verify.py`) and a rendered resume PDF before it will pre-fill anything for a given dedupe_key.
- Candidate-only questions are left blank rather than answered on the candidate's behalf: attestations and certifications, consent and privacy acknowledgements, legal work-authorization wording, demographic questions, and any question asking whether an AI agent filled the application.

## Browser automation can only read workspace files

The browser automation tools this command uses may only read files that live inside the workspace (this repository's checkout). This is why `pipeline/cli/render_resume.py` writes the tailored PDF under `data/resumes/` rather than, say, a temp directory or a path outside the repo - a resume upload control can only be pointed at a file the tool can actually read.

## Multiple applications in one run

Pass several dedupe_keys to fill several applications together: `/jsp-apply <key1> <key2> <key3>`. Each gets its own browser tab and its own tailored PDF attachment. The command works through the full list before reporting, then gives one combined summary (per-application filled/blank fields, plus how many were filled versus skipped) so the user can review and submit each in turn.

## What the user does

After `/jsp-apply` stops, every form in the run is filled and its browser tab left open. The user reviews every field - this is expected to take about two minutes per application - and clicks submit themselves. Nothing in this repository can do that final click for them.
