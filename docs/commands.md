# Commands

All commands live under `.claude/commands/` and run inside Claude Code from the repo root.

| Command | Stage | Does |
|---|---|---|
| `/jsp-daily` | Discovery, dedupe, hard filters, scoring | Polls company feeds, filters, scores, writes `data/matches/<date>.json`. |
| `/jsp-tailor <dedupe_key>` | Tailoring | Drafts a resume variant / answers for one match, verifies every claim traces to the profile, blocks on any violation. |
| `/jsp-apply <dedupe_key>` | Submission | Pre-fills the application form in the browser from a verified draft. Stops before submit. |
| `/jsp-track` | Tracking | Reads Gmail (read-only) to update `data/tracker.xlsx` statuses and flag 7-day follow-ups. |
| `/jsp-referrals <dedupe_key>` | Referrals | Finds 1-2 contacts at the target company and drafts an outreach note. Draft only - never sends. |

`<dedupe_key>` comes from an entry in `data/matches/<date>.json`, produced by `/jsp-daily`.

## Typical flow

1. `/jsp-daily` each morning (or scheduled - see [docs/daily-run.md](daily-run.md)).
2. For each match you want to pursue: `/jsp-tailor <key>`, then `/jsp-apply <key>`, then `/jsp-referrals <key>`.
3. Periodically: `/jsp-track` to sync statuses from Gmail and surface follow-ups.
