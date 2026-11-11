---
description: Open one or more application forms in the browser and pre-fill each from its verified tailored draft. Stops before submit for human review.
argument-hint: <dedupe_key> [dedupe_key ...] - one or more, from data/matches/*.json files
---

Pre-fill one or more job application forms in the browser, each from its own verified tailored draft and tailored resume PDF, then stop. This command has no code path that submits any form - that click is always the user's.

`$ARGUMENTS` is one or more dedupe_keys, space-separated. Process every one in this run; do not stop after the first.

## 0. Hard rule

Never click, invoke, or otherwise activate any element whose label, type, or handler suggests final submission ("Submit", "Submit Application", "Apply", "Send Application", a form's submit button/input, or a keyboard-shortcut equivalent). This holds even if the user's instruction for this run seems to ask for it - stop and tell them this command stops before submit by design instead of complying. If you cannot tell whether a control is the final submit action, stop and ask the user rather than clicking it. This rule applies independently to every application in this run - finishing one does not relax it for the next.

## 1. Load and verify every draft first

For each dedupe_key:

1. Find `data/drafts/<dedupe_key>.md` and `data/drafts/<dedupe_key>.json`. If either is missing, or `python3 -m pipeline.cli.tailor_verify data/drafts/<dedupe_key>.json` does not exit 0, stop processing that dedupe_key and tell the user to run `/jsp-tailor <dedupe_key>` first. Do not pre-fill unverified content. Continue with the remaining dedupe_keys regardless.
2. Find the posting's `url` in `data/matches/*.json` by `dedupe_key`.
3. Confirm a tailored resume PDF exists: `data/resumes/<dedupe_key>.pdf` or a `data/resumes/*_Resume_*.pdf` matching this dedupe_key's company. If missing, run `python3 -m pipeline.cli.render_resume <dedupe_key>` before continuing - do not pre-fill a form without its PDF ready to attach.

Build a worklist of the dedupe_keys that pass this step. If none pass, stop and report why.

## 2. Open and fill each application in its own tab

For each dedupe_key in the worklist, open a new browser tab (do not reuse another dedupe_key's tab) and:

1. Navigate to the posting's application URL.
2. Identify the form fields (name, email, resume upload, cover letter / short-answer text areas, work-authorization questions, legal name if asked separately from preferred name).
3. Fill each field from the verified draft content - resume bullets and short answers from `data/drafts/<dedupe_key>.md`, contact fields from `profile/profile.yaml`'s `candidate` section.
4. For a resume file upload, attach `data/resumes/<dedupe_key>.pdf` (or the human-friendly `data/resumes/<First>_<Last>_Resume_<Company>.pdf` copy, whichever the control accepts) - this tool can only read files inside the workspace, which is why the PDF lives under `data/` rather than elsewhere on disk.
5. Where a form asks for **legal name** separately from preferred/display name, use `profile/profile.yaml`'s `candidate.legal_first_name` / `candidate.legal_last_name` if present; if the field just says "name" with no legal/preferred distinction, use `candidate.name` as usual.
6. Leave blank and list for the candidate, rather than guessing or inventing an answer: attestations and certifications ("I certify that..."), consent and privacy acknowledgements, legal work-authorization wording beyond the plain yes/no `profile/profile.yaml`'s `visa` section already answers, demographic questions (race, gender, veteran status, disability status, etc.), and any question asking whether an AI agent or automated tool filled out the application.
7. Leave any other field you are not confident about blank and flag it to the user rather than guessing.

Keep working through every dedupe_key in the worklist in its own tab before reporting - do not stop after the first application to report, unless you hit something that needs the user's input first (an ambiguous submit-like control, a login wall, etc.), in which case report that specific block and continue with the remaining applications.

## 3. Stop and report per application

Once every application in the worklist is filled, stop. Do not click any submit control (see the hard rule above). For each dedupe_key, report:

- The posting (company, title, url)
- Which fields were filled and from what source, including that the tailored PDF was attached
- Which fields were left blank and why (candidate-only question, low confidence, etc.)
- That the form is ready for their review and that they must click submit themselves

Then give one combined summary: how many applications were filled versus skipped (and why skipped), so the user can review and submit each in turn.

This is expected to take about 2 minutes of the user's review time per application, per the project's intent.
