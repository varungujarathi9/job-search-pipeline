# Tracking

## The tracker spreadsheet

`data/tracker.xlsx` (gitignored) is a plain `.xlsx` file, openable directly in Excel or Google Sheets - no API integration, no Notion. Columns: `Company, Role, Date, Status, Contact, Next Action`.

`pipeline/tracker.py` provides the operations used by `/jsp-track` and can be called directly:

```
python3 -c "from pipeline.tracker import create_tracker; create_tracker()"       # create with headers
python3 -c "from pipeline.tracker import read_rows; [print(r) for r in read_rows()]"
python3 -c "from pipeline.tracker import append_row, TrackerRow; append_row(TrackerRow('Acme', 'Senior Backend Engineer', '2026-11-09', 'applied', '', ''))"
python3 -c "from pipeline.tracker import update_status; update_status('Acme', 'Senior Backend Engineer', 'interviewing')"
python3 -c "from pipeline.tracker import rows_needing_followup; [print(r) for r in rows_needing_followup()]"
```

Statuses: `applied, screening, interviewing, offer, rejected, withdrawn`.

## Gmail status parsing

`/jsp-track` reads Gmail, read-only, to infer status changes and flag rows with no response after 7+ days. It uses only read operations (search threads, get message/thread) - it never sends, replies, labels, or trashes anything, and the command's instructions say so explicitly.

### What a new user must connect

This repo relies on whatever Gmail connection Claude Code itself is configured with (e.g. the `claude.ai Gmail` MCP connector) - there is no separate OAuth setup script here. Before running `/jsp-track`:

1. Connect your Gmail account to Claude Code through its normal connector setup flow.
2. Confirm the connection is read-capable (search threads, get message/thread). No write/send scope is required or used.
3. Re-run `/jsp-track` any time after applying to pick up new status signals.

If Gmail is not connected, `/jsp-track` cannot search your mailbox; it will still read and report on the existing tracker contents and flag 7-day follow-ups from dates already in the spreadsheet.
