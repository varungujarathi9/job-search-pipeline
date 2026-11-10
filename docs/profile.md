# Profile

`profile/profile.yaml` (gitignored - copy from `profile/profile.example.yaml`) is the single source of fact for the whole pipeline. Scoring reads it to judge fit. Tailoring is only allowed to restate facts that appear here. See [docs/tailoring.md](tailoring.md) for how that is enforced.

## Fields

- `candidate` - name, email, phone, location, links. Used to fill contact fields in applications.
- `target.roles` - job titles you want. Used by scoring.
- `target.seniority_min` / `target.seniority_max` - one of `junior, mid, senior, staff, principal, manager, director`. Used by the hard seniority filter (`pipeline/hard_filters.py`).
- `target.locations`, `target.remote_ok`, `target.relocation_ok` - used by the hard location filter.
- `target.salary_floor_usd`, `target.salary_floor_basis` - used by scoring when a posting states compensation.
- `visa.needs_sponsorship` - used by the hard sponsorship filter. If `false`, the filter never excludes a posting on sponsorship language (sponsorship-related text is irrelevant to a candidate who does not need it).
- `dealbreakers` - free text. Not hard-filtered in code (hard filters are limited to location, seniority, sponsorship per the pipeline's design), but scoring is instructed to score near zero and explain when a dealbreaker shows up in a posting.
- `preferences` - industries and company stage, used as soft scoring signal.
- `accomplishments` - your master list. Each entry needs a unique, stable `id` (e.g. `acc-001`), a `title`, `metrics` (concrete, truthful numbers), `skills`, and `tags`. Tailoring can only restate a metric that literally appears in that entry's `title` or `metrics` text.
- `education`, `standard_answers` - supporting facts and reusable phrasing.

## Updating accomplishments

Add a new entry any time you have a new achievement to track; never delete an id a past tailored draft might still cite, unless you also know no saved draft references it - `pipeline/tailoring/verify.py` will correctly reject any draft that cites a removed id, but it is simpler to keep the list append-only.
