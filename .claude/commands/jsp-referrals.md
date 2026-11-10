---
description: Find 1-2 relevant people at a target company and draft a short referral-request note for the user to send themselves.
argument-hint: <dedupe_key from a data/matches/*.json file>
---

Find referral contacts for one match and draft an outreach note. This command only drafts text to a file - it has no tool call that sends a message, a connection request, or an email, to anyone, under any argument. If asked to send something, say this command only drafts and stop.

## 1. Load the match

Find the posting with dedupe_key `$1` in `data/matches/*.json`. If not found, stop and tell the user which files you checked.

## 2. Find 1-2 relevant people

Identify 1-2 people plausibly able to refer the candidate at that company: ideally someone on the same team, in a similar role, or who previously worked where the candidate worked (cross-reference `profile/profile.yaml`'s `accomplishments[].company` values for shared employer history).

Use public search only (e.g. web search for "<company> <team/role> LinkedIn") - do not log into or scrape LinkedIn, and do not use any saved LinkedIn session or credential. If you cannot confidently identify a real person from public search results, say so rather than inventing a name or title.

## 3. Draft the note

For each person found, draft a short (3-5 sentence) outreach note:

- Mentions the specific role (`title`, `company` from the match)
- Names one concrete, truthful point of connection (shared employer, shared skill area) - pull any factual claim about the candidate from `profile/profile.yaml`'s `accomplishments`, the same way `/jsp-tailor` does, rather than inventing rapport
- Asks for a referral or a short conversation, not a job
- Is written for the user to send themselves, in the user's voice, with no indication it was sent on their behalf

Save the draft(s) to `data/referrals/<dedupe_key>.md`, one note per identified person, each labeled with the person's name, role, and where they were found (e.g. a public profile URL).

## 4. Report

Tell the user how many contacts were found (0, 1, or 2), where to find the draft file, and remind them this is a draft only - they must review and send it themselves through their own LinkedIn/email account.
