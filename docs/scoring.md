# Dedupe, hard filters, and scoring

## Dedupe

`pipeline/dedupe.py` keys each posting by `(source, board_token, external_id)` - the ATS's own id, not title/company text, since the ATS id is stable across edits to a posting's text while free text is not. Seen keys persist in `data/seen_postings.json` across runs so a company's feed reappearing on the next day's poll does not resurface a posting already scored.

## Hard filters

`pipeline/hard_filters.py` runs before any LLM call, on every new posting, in this order:

1. **Location** - rejects an on-site posting outside `target.locations` unless `target.relocation_ok` is true; rejects a remote posting if `target.remote_ok` is false.
2. **Seniority** - parses the posting title for a seniority signal (junior/mid/senior/staff/principal/manager/director cues) and rejects if outside `[target.seniority_min, target.seniority_max]`. A title with no detectable signal is passed through for scoring to judge.
3. **Sponsorship** - only filters when `visa.needs_sponsorship` is true, and only rejects when the posting text explicitly states no sponsorship. A candidate who does not need sponsorship is never filtered on this axis.

A posting failing any filter is dropped with its reason and never reaches scoring. This mirrors the project's intent: hard filters first, LLM scoring only on what survives.

## Scoring

Scoring is performed by Claude Code itself (`.claude/commands/jsp-daily.md`), not a separate model API call from Python code - the agent reads `data/filtered_postings.json` and `profile/profile.yaml` and assigns each posting a 0-100 score with a rationale, using `pipeline/scoring.py`'s `ScoredPosting` as the output shape. Scoring additionally screens for `dealbreakers` language, which the hard filters do not check (dealbreakers are free text, not a structured field).

Each day's top 5-10 (score >= 60, or down to 40 if fewer than 5 clear 60) are written to `data/matches/<date>.json`.
