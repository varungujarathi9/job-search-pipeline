---
description: Generate a tailored resume variant and short answers for one match, with every claim verified against the master accomplishments list.
argument-hint: <dedupe_key from a data/matches/*.json file>
---

Generate tailored application material for one posting, with every factual claim enforced against `profile/profile.yaml` - not merely prompted to avoid inventing facts.

## 1. Load inputs

Find the posting with dedupe_key `$1` in `data/matches/*.json` (search all dated files if needed) and load `profile/profile.yaml`.

If the dedupe_key is not found, stop and tell the user which matches files you checked.

## 2. Draft claims against the schema, not prose

Do not draft a resume as free text first. Build a `TailoredOutput` JSON object directly, matching `pipeline.tailoring.schema.TailoredOutput.to_dict()`:

```json
{
  "target_company": "...",
  "target_role": "...",
  "claims": [
    {"text": "...", "source_kind": "accomplishment", "source_ref": "acc-001"},
    {"text": "...", "source_kind": "candidate_fact", "source_ref": "candidate.name"},
    {"text": "...", "source_kind": "boilerplate", "source_ref": null}
  ]
}
```

Rules while drafting, enforced mechanically in the next step - do not rely on getting these right from memory alone:

- `accomplishment` claims: `source_ref` must be a real `accomplishments[].id` from the profile. Only restate numbers that literally appear in that accomplishment's `title` or `metrics` - do not round up, combine two accomplishments' numbers, or invent a number that sounds plausible.
- `candidate_fact` claims: `source_ref` is a dotted field path into the profile (e.g. `candidate.name`, `candidate.email`, `education.0.degree`). The claim's `text` must equal that field's actual value exactly - no extra words. For a list field, `text` must equal exactly one element; to cite several values from the same list field, write one claim per value instead of combining them. The gate blocks any `candidate_fact` claim whose text is padded with content beyond a single resolved value. Write any descriptive sentence (experience, achievements, biography) as an `accomplishment` claim instead.
- `boilerplate` claims: connective text only ("I'm excited to apply because..."). No numbers, no company names, no skill names - those need a real `source_ref` instead.

Select and order accomplishments by relevance to the posting's title/description, but never alter their text's factual content.

Save the draft to `data/drafts/<dedupe_key>.json`.

## 3. Verify - this is the gate, not a suggestion

Run:

```
python3 -m pipeline.cli.tailor_verify data/drafts/<dedupe_key>.json
```

If it exits non-zero, it printed every offending claim and why. Fix those specific claims (change the `source_ref`, or move the claim to `boilerplate` and strip the fact, or drop it) and re-run the verifier. Do not present, save elsewhere, or tell the user the material is ready until this command exits 0. Do not hand-wave past a violation - each one names the exact claim text and reason.

## 4. Render human-readable output and report

Once verified, render the claims into a short resume-bullet list and a response to any application question the user named, and save that rendering to `data/drafts/<dedupe_key>.md`. Tell the user the verification passed, show the rendered content, and name both saved file paths.
