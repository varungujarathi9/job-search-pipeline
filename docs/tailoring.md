# Tailoring

Tailoring must never invent a claim. This is enforced by code, not only by prompting.

## The contract

`/jsp-tailor` builds output as structured claims (`pipeline/tailoring/schema.py`), not free-text prose. Each claim has a `source_kind` and a `source_ref`:

- `accomplishment` - `source_ref` must be a real `accomplishments[].id` in `profile/profile.yaml`. Any number in the claim's text must also appear in that accomplishment's `title` or `metrics` text.
- `candidate_fact` - `source_ref` is a dotted field path into the profile (e.g. `candidate.name`). The claim's text, once normalized for case and whitespace, must equal the resolved field's value exactly - no padding with other words. If the field is a list, the text must equal one element, or (when split on commas, semicolons, or " and ") every resulting segment must equal an element. A `candidate_fact` claim cannot carry any descriptive or biographical content beyond the field's literal value - that belongs in an `accomplishment` claim instead.
- `boilerplate` - connective text with no factual content: no digits, and no token matching any accomplishment's skill, tag, or company name.

## The gate

`pipeline/tailoring/verify.py`'s `verify_output` checks every claim against the rules above. `pipeline/cli/tailor_verify.py` is the CLI wrapper `/jsp-tailor` calls after drafting - it exits non-zero and prints every offending claim's text and reason if any claim fails. The command is instructed to keep fixing and re-running until it exits 0, and never to present or save unverified output.

This catches both failure modes: a fabricated accomplishment id, and a real id cited with an inflated or altered number (e.g. citing accomplishment `acc-001` but writing "90%" when the profile says "32%"). It also catches a `candidate_fact` claim that cites a real field path but writes text unrelated to that field's value (e.g. citing `candidate.name` while writing "Won a Nobel Prize in Physics"), and a `candidate_fact` claim that pads a real value with fabricated extra content (e.g. citing `target.roles` while writing "Senior Backend Engineer with 20 years at NASA").

## What this does not catch

The verifier checks numeric and identity traceability, not qualitative truthfulness - it cannot tell you whether a claim is a fair paraphrase of the cited accomplishment's prose. Review the rendered `data/drafts/<dedupe_key>.md` yourself before using it.

## Resume file generation

This repo does not currently generate a PDF/DOCX resume file. `/jsp-apply` points you at the verified Markdown draft to incorporate into your own resume document and upload yourself.
