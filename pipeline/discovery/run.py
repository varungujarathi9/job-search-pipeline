"""Poll every configured company's job board feed and return all postings."""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import Any

import yaml

from pipeline.discovery import FETCHERS
from pipeline.postings import Posting

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_COMPANIES_PATH = REPO_ROOT / "config" / "companies.yaml"

logger = logging.getLogger(__name__)


class CompaniesConfigError(ValueError):
    pass


@dataclasses.dataclass
class FetchFailure:
    company: str
    ats: str
    board_token: str
    error: str


@dataclasses.dataclass
class DiscoveryResult:
    postings: list[Posting]
    failures: list[FetchFailure]


def load_companies(path: Path | None = None) -> list[dict[str, Any]]:
    companies_path = path or DEFAULT_COMPANIES_PATH
    if not companies_path.exists():
        raise CompaniesConfigError(
            f"Company list not found at {companies_path}. "
            "Copy companies.example.yaml to companies.yaml and add your target companies."
        )
    with companies_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    companies = (data or {}).get("companies", [])
    if not isinstance(companies, list):
        raise CompaniesConfigError("companies.yaml must have a top-level 'companies' list.")
    for entry in companies:
        if entry.get("ats") not in FETCHERS:
            raise CompaniesConfigError(
                f"Unsupported ats '{entry.get('ats')}' for company '{entry.get('name')}'. "
                f"Supported: {sorted(FETCHERS)}."
            )
    return companies


def run_discovery(companies: list[dict[str, Any]] | None = None) -> DiscoveryResult:
    companies = companies if companies is not None else load_companies()
    postings: list[Posting] = []
    failures: list[FetchFailure] = []

    for entry in companies:
        name = entry["name"]
        ats = entry["ats"]
        board_token = entry["board_token"]
        fetcher = FETCHERS[ats]
        try:
            postings.extend(fetcher(name, board_token))
        except Exception as exc:  # noqa: BLE001 - one bad board must not kill the run
            logger.warning("Failed to fetch %s (%s/%s): %s", name, ats, board_token, exc)
            failures.append(FetchFailure(company=name, ats=ats, board_token=board_token, error=str(exc)))

    return DiscoveryResult(postings=postings, failures=failures)
