---
description: Scan Gmail (read-only) for application status updates and flag 7-day follow-ups, then update the tracker spreadsheet.
---

Update `data/tracker.xlsx` from Gmail activity and flag overdue follow-ups. This command only reads Gmail - it never sends, labels as spam, or deletes anything, and it never calls a Gmail write/send tool.

## 1. Read the tracker

Read `data/tracker.xlsx` via:

```
python3 -c "from pipeline.tracker import read_rows; [print(r) for r in read_rows()]"
```

If it does not exist yet, run `python3 -c "from pipeline.tracker import create_tracker; create_tracker()"` to create it with headers, then tell the user it is empty and stop - there is nothing to match against Gmail yet.

## 2. Search Gmail for status signals (read-only)

For each row with status in `applied`, `screening`, or `interviewing`, use the Gmail search tool to look for recent messages from or about that company: search subject/body for the company name plus terms like "interview", "assessment", "offer", "unfortunately", "not moving forward", "regret". Use only read operations (search threads, get message/thread) - never reply, send, forward, label, or trash.

Classify what you find conservatively:

- Rejection language -> candidate new status `rejected`
- Interview/screening scheduling language -> candidate new status `screening` or `interviewing` (pick the more advanced of the two if ambiguous)
- Offer language -> candidate new status `offer`
- Nothing found, or ambiguous -> leave status unchanged

Do not guess from a single ambiguous word; prefer leaving a row unchanged over a wrong status change. Note the triggering email's subject/date as the evidence for any change you make.

## 3. Apply status updates

For each row whose status should change, run:

```
python3 -c "from pipeline.tracker import update_status; print(update_status('<company>', '<role>', '<new_status>', '<next_action>'))"
```

Set `next_action` to a short human-actionable note (e.g. "Prep for technical screen", "Send thank-you note").

## 4. Flag 7-day follow-ups

Run:

```
python3 -c "from pipeline.tracker import rows_needing_followup; [print(r) for r in rows_needing_followup()]"
```

This returns rows still `applied` with no response for 7+ days. For each, update its `next_action` to something like "Follow up - no response in 7+ days" via `update_status`, keeping status as `applied`.

## 5. Report

Summarize to the user: how many rows were checked, how many status changes were made (with the Gmail evidence for each), and how many rows are now flagged for follow-up. Remind them that Gmail access here is read-only and this command never sends a message - see `docs/tracking.md` for what a new user must connect before this command works.
