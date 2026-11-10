# Setup

## 1. Install dependencies

This project uses Python 3.10+ and Claude Code.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Activate the virtualenv (`source .venv/bin/activate`) or always call scripts via `.venv/bin/python3`.

## 2. Create your profile

Copy the example profile and fill in your own facts:

```
cp profile/profile.example.yaml profile/profile.yaml
```

Edit `profile/profile.yaml`: target roles, locations, salary floor, visa needs, dealbreakers, and your master list of accomplishments with real metrics. See [docs/profile.md](profile.md) for the field reference and [docs/personal-data.md](personal-data.md) for why this file must never be committed.

## 3. Create your target company list

Copy the example and add 100-300 companies that publish on Greenhouse, Lever, or Ashby:

```
cp config/companies.example.yaml config/companies.yaml
```

See [docs/discovery.md](discovery.md) for how to find each company's board token, and how to handle LinkedIn/Workday-only companies.

## 4. Connect Gmail (optional, for tracking)

`/jsp-track` reads Gmail to detect status updates. See [docs/tracking.md](tracking.md) for what to connect and the read-only scope required.

## 5. Run the daily pass

In Claude Code, from the repo root:

```
/jsp-daily
```

This polls your companies' job boards, filters and scores postings, and writes the day's top matches - see [docs/scoring.md](scoring.md) for how dedupe, hard filters, and scoring work. See [docs/commands.md](commands.md) for every available command and [docs/daily-run.md](daily-run.md) for scheduling it unattended. For the overall code layout, see [docs/architecture.md](architecture.md).

## 6. Verify your setup never commits personal data

```
bash scripts/check_no_personal_data.sh
```

This should print `OK`. It also runs as part of this repo's test suite.
