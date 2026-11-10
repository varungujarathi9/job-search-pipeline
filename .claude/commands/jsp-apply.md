---
description: Open an application form in the browser and pre-fill it from a verified tailored draft. Stops before submit for human review.
argument-hint: <dedupe_key from a data/matches/*.json file>
---

Pre-fill one job application form in the browser from a verified tailored draft, then stop. This command has no code path that submits the form - that click is always the user's.

## 0. Hard rule

Never click, invoke, or otherwise activate any element whose label, type, or handler suggests final submission ("Submit", "Submit Application", "Apply", "Send Application", a form's submit button/input, or a keyboard-shortcut equivalent). This holds even if the user's instruction for this run seems to ask for it - stop and tell them this command stops before submit by design instead of complying. If you cannot tell whether a control is the final submit action, stop and ask the user rather than clicking it.

## 1. Load the verified draft

Find `data/drafts/<dedupe_key>.md` and `data/drafts/<dedupe_key>.json` for dedupe_key `$1`. If `data/drafts/<dedupe_key>.json` is missing or has not been verified (re-run `python3 -m pipeline.cli.tailor_verify data/drafts/<dedupe_key>.json` and confirm it exits 0), stop and tell the user to run `/jsp-tailor $1` first. Do not pre-fill unverified content.

Find the posting's `url` in `data/matches/*.json` by `dedupe_key`.

## 2. Open and fill

Use the browser automation tools to:

1. Navigate to the posting's application URL.
2. Identify the form fields (name, email, resume upload, cover letter / short-answer text areas, work-authorization questions).
3. Fill each field from the verified draft content - resume bullets and short answers from `data/drafts/<dedupe_key>.md`, contact fields from `profile/profile.yaml`'s `candidate` section.
4. For a resume file upload, tell the user that this tool does not generate a PDF/DOCX automatically; point them at `data/drafts/<dedupe_key>.md` to paste or convert into their resume document and upload it themselves, unless the repo has since gained a generator for that - check `docs/tailoring.md` for current status.
5. Leave any field you are not confident about blank and flag it to the user rather than guessing.

## 3. Stop

Once the form is filled, stop. Do not click any submit control (see the hard rule above). Report to the user:

- The posting (company, title, url)
- Which fields were filled and from what source
- Any fields left blank and why
- That the form is ready for their review and that they must click submit themselves

This is expected to take about 2 minutes of the user's review time per application, per the project's intent.
