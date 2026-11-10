# Referrals

`/jsp-referrals` finds 1-2 people plausibly able to refer the candidate at a target company and drafts a short outreach note for each, saved to `data/referrals/<dedupe_key>.md`.

## Draft-only, by design

Nothing in this repository sends a message, a connection request, or an email on the user's behalf. The command's instructions state this explicitly and refuse to treat any user instruction as a request to send. The user reviews and sends each note themselves, through their own LinkedIn or email account.

## How contacts are found

Only public web search - no LinkedIn login, scraping, or saved session. If no person can be confidently identified, the command says so rather than inventing a name.

## Factual honesty

Any claim about the candidate in a drafted note follows the same sourcing discipline as `/jsp-tailor` (see [docs/tailoring.md](tailoring.md)): a point of connection must be a real fact pulled from `profile/profile.yaml`, not an invented rapport point.
