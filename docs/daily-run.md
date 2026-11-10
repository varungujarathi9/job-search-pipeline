# Scheduling the daily run

`/jsp-daily` is a single command covering discovery, dedupe, hard filters, and scoring - designed to run unattended on a schedule.

## cron example

```cron
0 7 * * * cd /path/to/job-search-pipeline && claude -p "/jsp-daily" >> data/logs/daily.log 2>&1
```

Adjust the path and time to your setup. `data/logs/` is inside the gitignored `data/` directory.

## Requirements for an unattended run

- `profile/profile.yaml` and `config/companies.yaml` must already exist (see [docs/setup.md](setup.md)) - the command errors out naming the missing file otherwise rather than guessing defaults.
- The machine running cron needs network access to `boards-api.greenhouse.io`, `api.lever.co`, and `api.ashbyhq.com`.
- `claude` must be authenticated non-interactively in that environment, per your Claude Code setup.

## What it does not do unattended

`/jsp-daily` only discovers and scores - it never tailors, applies, tracks, or drafts referrals on its own. Those commands take a specific `dedupe_key` argument and are meant to be run interactively once you decide which matches to pursue.
