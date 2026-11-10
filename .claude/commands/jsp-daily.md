---
description: Run the daily discovery, dedupe, hard-filter, and LLM-scoring pass and surface the top matches.
---

Run the daily job-search discovery and scoring pass. This command is designed to be scheduled (e.g. via cron invoking `claude -p "/jsp-daily"`).

## 1. Run discovery, dedupe, and hard filters

Run:

```
python3 -m pipeline.cli.discover
```

This polls every company in `config/companies.yaml` across Greenhouse, Lever, and Ashby, drops postings already seen on a prior run, and drops postings failing the deterministic hard filters (location, seniority, sponsorship) defined in `pipeline/hard_filters.py`. It writes the survivors to `data/filtered_postings.json`.

If `config/companies.yaml` or `profile/profile.yaml` does not exist yet, the command will print an error naming which example file to copy. Stop and tell the user to set those up before continuing.

If it reports fetch warnings for specific companies (a dead board token, a network error), note them but continue - a handful of unreachable boards should not block scoring the postings that did come back.

## 2. Score every filtered posting against the profile

Read `data/filtered_postings.json` and `profile/profile.yaml`.

For each posting, score it 0-100 for fit against the profile's `target.roles`, `target.locations`, `dealbreakers`, `preferences`, and the seniority/location/sponsorship context already established by the hard filters (do not re-derive those - they already passed). Score on:

- Role/title alignment with `target.roles`
- Overlap between the posting's described responsibilities and the candidate's `accomplishments` skills/tags
- Company fit against `preferences.industries_preferred` / `industries_avoided` / `company_stage_preferred` when inferable from the posting
- Any `dealbreakers` language appearing in the posting description (score near 0 and say why, even though dealbreakers are free text and not hard-filtered in code)

Write a one-paragraph rationale per posting citing the specific signal that drove the score.

## 3. Write today's matches file

Take the top 5-10 scored postings (score >= 60, capped at 10; if fewer than 5 clear 60, include down to a minimum score of 40 to still reach 5 when possible, and say in the output when the bar was lowered to fill the list).

Write them to `data/matches/<YYYY-MM-DD>.json` as a JSON array of objects matching `pipeline.scoring.ScoredPosting.to_dict()`'s shape: `dedupe_key, company, title, location, url, score, rationale`.

## 4. Report to the user

Print a short numbered list: company, title, location, score, one-line rationale, url. Tell the user the matches file path. Mention how many postings were fetched, how many survived dedupe/filters, and how many fetch warnings (if any) occurred.

Do not generate resumes, tailored answers, or referral notes in this command - those are separate steps (`/jsp-tailor` and `/jsp-referrals`) run per-match once the user picks which ones to pursue.
