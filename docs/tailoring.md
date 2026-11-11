# Tailoring

Tailoring must never invent a claim. This is enforced by code, not only by prompting.

## The contract

`/jsp-tailor` builds output as structured claims (`pipeline/tailoring/schema.py`), not free-text prose. Each claim has a `source_kind` and a `source_ref`:

- `accomplishment` - `source_ref` must be a real `accomplishments[].id` in `profile/profile.yaml`. Any number in the claim's text must also appear in that accomplishment's `title` or `metrics` text.
- `candidate_fact` - `source_ref` is a dotted field path into the profile (e.g. `candidate.name`). The claim's text, once normalized for case and whitespace, must equal the resolved field's value exactly - no padding with other words. If the field is a list, the text must equal exactly one element of that list; to cite more than one value, write a separate claim per value rather than joining them in one claim's text. A `candidate_fact` claim cannot carry any descriptive or biographical content beyond the field's literal value - that belongs in an `accomplishment` claim instead.
- `boilerplate` - connective text with no factual content: no digits, and no token matching any accomplishment's skill, tag, or company name.

## The gate

`pipeline/tailoring/verify.py`'s `verify_output` checks every claim against the rules above. `pipeline/cli/tailor_verify.py` is the CLI wrapper `/jsp-tailor` calls after drafting - it exits non-zero and prints every offending claim's text and reason if any claim fails. The command is instructed to keep fixing and re-running until it exits 0, and never to present or save unverified output.

This catches both failure modes: a fabricated accomplishment id, and a real id cited with an inflated or altered number (e.g. citing accomplishment `acc-001` but writing "90%" when the profile says "32%"). It also catches a `candidate_fact` claim that cites a real field path but writes text unrelated to that field's value (e.g. citing `candidate.name` while writing "Won a Nobel Prize in Physics"), and a `candidate_fact` claim that pads a real value with fabricated extra content (e.g. citing `target.roles` while writing "Senior Backend Engineer with 20 years at NASA").

## What this does not catch

The verifier checks numeric and identity traceability, not qualitative truthfulness - it cannot tell you whether a claim is a fair paraphrase of the cited accomplishment's prose. Review the rendered `data/drafts/<dedupe_key>.md` yourself before using it.

## Resume PDF generation

`pipeline/cli/render_resume.py` (invoked as `python3 -m pipeline.cli.render_resume <dedupe_key>`, called by `/jsp-tailor` after verification passes) renders a one-page US Letter resume PDF from a verified draft. It re-runs `verify_output` itself and refuses to render if the draft doesn't pass, so a PDF can never be produced from unverified content even if called directly.

It uses only two sources of text: `profile/profile.yaml` facts (contact line, education, skills, accomplishment/project title and metrics as a fallback) and the verified draft's own claim text (preferred, where a claim cites that accomplishment). See `pipeline/resume.py` for the layout rules: accomplishments grouped under their role in reverse-chronological order, bullets within a role ordered by the draft's relevance order, skills reordered to put any group mentioned in the draft's claims first, plus education and projects sections.

It writes `data/resumes/<dedupe_key>.pdf` (canonical name) and a human-friendly copy `data/resumes/<First>_<Last>_Resume_<Company>.pdf` - `/jsp-apply` attaches the latter to the application's resume upload.

**Why reportlab, not a headless browser:** rendering goes through `reportlab` (pure Python, pinned in `requirements.txt`), not an HTML-to-PDF conversion via a locally installed Chrome/Chromium. A pure-Python dependency installs the same way as the rest of this project's requirements and has no dependency on a browser binary being present or at a particular version; it also keeps PDF generation out of the browser-automation tool entirely (see docs/submission.md for why that tool is restricted to files inside the workspace).
