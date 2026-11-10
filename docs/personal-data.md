# Personal data

This repository is public. No personal data is ever committable - every path listed below is gitignored, and `scripts/check_no_personal_data.sh` fails the build if any of them become tracked.

## Gitignored paths

- `profile/profile.yaml` - your real target roles, locations, salary floor, visa status, dealbreakers, and master accomplishments list.
- `config/companies.yaml` - your real target company list.
- `data/` - all runtime output: fetched and scored postings, the tracker spreadsheet, generated resume drafts and referral notes, and the dedupe store.
- Any `.env`, `credentials.json`, or `token.json` - local credentials.

## What is committed instead

- `profile/profile.example.yaml` - a fictional profile showing the schema.
- `config/companies.example.yaml` - a fictional company list showing the schema.
- `fixtures/` - fictional job board API responses used by the test suite.

## The check

Run `bash scripts/check_no_personal_data.sh` any time. It inspects `git ls-files` for the patterns above and exits non-zero naming any violation. It is part of the test suite (`tests/test_no_personal_data_guard.py`) so CI fails if a personal path is ever accidentally staged and committed.

If you fork this repo and accidentally commit a personal file, remove it from history (not just the working tree) before pushing anywhere public - a `git rm --cached` plus a new commit still leaves the data in prior commits.
