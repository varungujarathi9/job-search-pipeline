# Discovery

Discovery polls each target company's public job board API directly. It never scrapes a job board site (Indeed, LinkedIn, etc.) or a company's careers page HTML - only the three ATS vendors' documented public JSON APIs:

- **Greenhouse**: `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`
- **Lever**: `https://api.lever.co/v0/postings/{board_token}?mode=json`
- **Ashby**: `https://api.ashbyhq.com/posting-api/job-board/{board_token}`

These are public, unauthenticated, intended-for-this-purpose endpoints - the same ones each vendor's own embeddable job board widget calls.

## Finding a company's board token

- Greenhouse: the token in `https://boards.greenhouse.io/<token>`.
- Lever: the slug in `https://jobs.lever.co/<slug>`.
- Ashby: the name in `https://jobs.ashbyhq.com/<name>`.

If a company's careers page does not match one of those three URL patterns, it is not on a supported ATS - see "LinkedIn and Workday companies" below.

## Your company list

Copy `config/companies.example.yaml` to `config/companies.yaml` (gitignored) and list 100-300 companies, each with `name`, `ats` (`greenhouse`, `lever`, or `ashby`), and `board_token`.

## Running discovery

```
python3 -m pipeline.cli.discover
```

This fetches every company's feed, drops postings already seen on a prior run (tracked in `data/seen_postings.json`), drops postings failing the hard filters in `pipeline/hard_filters.py`, and writes survivors to `data/filtered_postings.json`. A single unreachable board prints a warning and does not stop the run - see the printed summary for fetch failures.

`/jsp-daily` runs this as its first step, then scores the result.

## LinkedIn and Workday companies

LinkedIn and Workday-based company postings are explicitly out of scope for automated polling - this pipeline does not scrape either. For a target company on one of those platforms, set up a LinkedIn saved-search job alert (emailed to you) or a Workday career-site alert instead, and triage those emails yourself alongside the daily `/jsp-daily` output. Nothing in this repo reads those alert emails automatically.
