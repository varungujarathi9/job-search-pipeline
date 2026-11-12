# Submission

`/jsp-apply <dedupe_key> [dedupe_key ...]` uses browser automation to open one or more postings' application pages, each in its own tab, and pre-fill each from its verified tailored draft and tailored resume PDF (see [docs/tailoring.md](tailoring.md)). It never submits.

## Why this is safe by construction

- The command's instructions name the exact submit-labeled controls it must never click, and tell the agent to stop and ask rather than guess when a control's purpose is unclear. This holds per application - finishing one form never relaxes the rule for the next.
- There is no "auto-submit" mode, flag, or argument - the command has exactly one path, and it ends at "stop" after filling every form in the run.
- The command requires a verified draft (`/jsp-tailor` must have already passed `pipeline/cli/tailor_verify.py`) and a rendered resume PDF before it will pre-fill anything for a given dedupe_key.
- Only consent and privacy acknowledgement checkboxes and attestation/certification statements ("I certify that...", "I agree to...") are left blank for the candidate, and only because this agent's own operating rules don't let it agree to legal terms on someone else's behalf. The per-application report calls out any of these that are marked required, since the user must check them before the form can submit.

## Required fields

Every required field the command can answer from `profile/profile.yaml`, `profile/profile.yaml`'s `standard_answers` section, or the verified draft is always filled - not skipped just because it takes more than a literal copy-paste (selecting the closest matching option in a required dropdown, checking a required checkbox whose statement is true per the profile, and so on). This includes:

- Plain work-authorization and age questions, from `standard_answers.work_authorized_us`, `standard_answers.age_18_or_older`, and `visa.needs_sponsorship` / `visa.work_authorization`.
- Demographic questions (race, gender, veteran status, disability status, etc.) - the command never invents a demographic answer, but when the form offers a decline-to-answer option ("I don't wish to answer", "Prefer not to say"), it selects that option rather than leaving the field blank. Only a required demographic question with no decline option stays blank.
- The "did an AI agent fill out this application" question (or similar) - answered truthfully as **Yes**, never left blank.

"Required" is not itself a reason to leave a field blank; only the consent/attestation category above is. The per-application report calls out any required field that was left blank, since the user will need to fill it themselves before the form can submit.

## Browser automation can only read workspace files

The browser automation tools this command uses may only read files that live inside the workspace (this repository's checkout). This is why `pipeline/cli/render_resume.py` writes the tailored PDF under `data/resumes/` rather than, say, a temp directory or a path outside the repo - a resume upload control can only be pointed at a file the tool can actually read.

## Multiple applications in one run

Pass several dedupe_keys to fill several applications together: `/jsp-apply <key1> <key2> <key3>`. Each gets its own browser tab and its own tailored PDF attachment. The command works through the full list before reporting, then gives one combined summary (per-application filled/blank fields, plus how many were filled versus skipped) so the user can review and submit each in turn.

## What the user does

After `/jsp-apply` stops, every form in the run is filled and its browser tab left open. The user reviews every field - this is expected to take about two minutes per application - and clicks submit themselves. Nothing in this repository can do that final click for them.
