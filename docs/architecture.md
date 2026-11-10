# Architecture

## Layout

- `pipeline/` - Python package. Deterministic logic: discovery (feed fetchers), dedupe, hard filters, the tracker spreadsheet, and the tailoring claim verifier. No LLM calls live here.
- `.claude/commands/` - Claude Code slash commands. Each wraps one pipeline stage, and is where the agent itself does the parts that need judgment (scoring, drafting, browser filling, Gmail triage).
- `profile/`, `config/` - real files gitignored, `.example.yaml` templates committed. See [docs/personal-data.md](personal-data.md).
- `data/` - all runtime output, entirely gitignored.
- `fixtures/` - fictional job board API responses used by the test suite.
- `tests/` - `unittest`-based tests, run with `python3 -m unittest discover -s tests`.
- `scripts/check_no_personal_data.sh` - fails if a personal path is tracked by git.

## Why some logic is Python and some is a Claude Code command

Hard filters, dedupe, and claim verification are deterministic and must never depend on a model call succeeding or being consistent across runs - the only sturdy way to enforce "an untraceable claim is blocked" is executable code with its own test suite. Those live in `pipeline/` and have no outbound dependency on Claude Code.

Scoring, tailoring drafting, browser form-filling, Gmail-signal interpretation, and referral-contact discovery are judgment calls best made by the agent reading current context (a posting's full text, a user's existing resume phrasing, an email thread). Those live in `.claude/commands/`, and where a judgment call produces a factual claim, the command is required to run it back through the Python verifier before it can reach the user.

## Out of scope

- Automatic submission of any application - see [docs/submission.md](submission.md).
- Sending any message, connection request, or email - see [docs/referrals.md](referrals.md) and [docs/tracking.md](tracking.md).
- Hosted services or a web UI - this is a local, cloned repo run through Claude Code.
- Job sources beyond Greenhouse, Lever, Ashby, and LinkedIn/Workday saved-search email alerts - see [docs/discovery.md](discovery.md).
- Notion or Google Sheets API integration for tracking - the tracker is a local `.xlsx` file.
