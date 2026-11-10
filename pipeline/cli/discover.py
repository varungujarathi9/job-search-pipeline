"""CLI: poll all configured job boards, dedupe against prior runs, apply hard
filters, and write the surviving postings to data/filtered_postings.json for
the /jsp-daily Claude Code command to score.

Usage:
    python -m pipeline.cli.discover
    python -m pipeline.cli.discover --companies path/to/companies.yaml --profile path/to/profile.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline.dedupe import dedupe_postings, load_seen_keys, save_seen_keys
from pipeline.discovery.run import CompaniesConfigError, load_companies, run_discovery
from pipeline.hard_filters import apply_hard_filters
from pipeline.profile import ProfileError, load_profile

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_PATH = REPO_ROOT / "data" / "filtered_postings.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companies", type=Path, default=None, help="Path to companies.yaml")
    parser.add_argument("--profile", type=Path, default=None, help="Path to profile.yaml")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--no-save-seen",
        action="store_true",
        help="Do not persist newly-seen dedupe keys (useful for dry runs)",
    )
    args = parser.parse_args(argv)

    try:
        companies = load_companies(args.companies)
        profile = load_profile(args.profile)
    except (CompaniesConfigError, ProfileError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = run_discovery(companies)
    for failure in result.failures:
        print(
            f"warning: failed to fetch {failure.company} ({failure.ats}/{failure.board_token}): {failure.error}",
            file=sys.stderr,
        )

    seen_keys = load_seen_keys()
    new_postings, updated_keys = dedupe_postings(result.postings, seen_keys)

    filter_results = apply_hard_filters(new_postings, profile)
    passed = [r.posting for r in filter_results if r.passed]
    dropped = [r for r in filter_results if not r.passed]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in passed], f, indent=2)

    if not args.no_save_seen:
        save_seen_keys(updated_keys)

    print(f"fetched {len(result.postings)} postings across {len(companies)} companies")
    print(f"{len(new_postings)} new after dedupe, {len(passed)} passed hard filters, {len(dropped)} dropped")
    print(f"wrote {len(passed)} filtered postings to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
