"""Deterministic hard filters applied before LLM scoring.

These filters run first so the LLM scoring step (pipeline/scoring.py) only
ever sees postings that already pass location, seniority, and sponsorship
checks. A posting that fails any filter is dropped with a reason, never
passed to the model.
"""

from __future__ import annotations

import dataclasses
import re

from pipeline.postings import Posting
from pipeline.profile import Profile

SENIORITY_LEVELS = ["junior", "mid", "senior", "staff", "principal", "manager", "director"]

SENIORITY_TITLE_PATTERNS: dict[str, list[str]] = {
    "junior": [r"\bjunior\b", r"\bentry[- ]level\b", r"\bassociate\b", r"\bI\s*$"],
    "mid": [r"\bmid[- ]level\b", r"\bII\b"],
    "senior": [r"\bsenior\b", r"\bsr\.?\b", r"\bIII\b"],
    "staff": [r"\bstaff\b", r"\blead\b"],
    "principal": [r"\bprincipal\b"],
    "manager": [r"\bmanager\b", r"\bEM\b"],
    "director": [r"\bdirector\b", r"\bhead of\b", r"\bVP\b"],
}

NO_SPONSORSHIP_PATTERNS = [
    r"\bno (?:visa )?sponsorship\b",
    r"\bsponsorship (?:is )?not (?:available|provided|offered)\b",
    r"\bunable to (?:provide|offer) (?:visa )?sponsorship\b",
    r"\bmust be (?:a )?(?:us citizen|authorized to work)\b",
]

OFFERS_SPONSORSHIP_PATTERNS = [
    r"\bwe (?:can |will )?sponsor\b",
    r"\bsponsorship (?:is )?available\b",
    r"\bvisa sponsorship (?:provided|offered)\b",
]


@dataclasses.dataclass
class FilterResult:
    posting: Posting
    passed: bool
    reasons: list[str]


def _title_seniority(title: str) -> str | None:
    for level, patterns in SENIORITY_TITLE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return level
    return None


def _seniority_in_range(level: str, floor: str, ceiling: str) -> bool:
    try:
        lo = SENIORITY_LEVELS.index(floor)
        hi = SENIORITY_LEVELS.index(ceiling)
        idx = SENIORITY_LEVELS.index(level)
    except ValueError:
        return True  # unrecognized level in config - do not filter on it
    return lo <= idx <= hi


def check_seniority(posting: Posting, profile: Profile) -> tuple[bool, str | None]:
    level = _title_seniority(posting.title)
    if level is None:
        return True, None  # cannot determine from title - let scoring judge it
    floor = profile.target.get("seniority_min", SENIORITY_LEVELS[0])
    ceiling = profile.target.get("seniority_max", SENIORITY_LEVELS[-1])
    if _seniority_in_range(level, floor, ceiling):
        return True, None
    return False, f"seniority '{level}' outside target range [{floor}, {ceiling}]"


def check_location(posting: Posting, profile: Profile) -> tuple[bool, str | None]:
    target = profile.target
    remote_ok = target.get("remote_ok", False)
    target_locations = [loc.lower() for loc in target.get("locations", [])]
    posting_location = (posting.location or "").lower()

    if not posting_location:
        return True, None  # unknown location - let scoring judge it

    is_remote_posting = "remote" in posting_location
    if is_remote_posting:
        if remote_ok:
            return True, None
        return False, f"posting is remote ('{posting.location}') but remote_ok is false"

    for target_loc in target_locations:
        if target_loc in posting_location or posting_location in target_loc:
            return True, None

    if target.get("relocation_ok", False):
        return True, None

    return False, f"location '{posting.location}' not in target locations and relocation_ok is false"


def check_sponsorship(posting: Posting, profile: Profile) -> tuple[bool, str | None]:
    needs_sponsorship = profile.visa.get("needs_sponsorship", False)
    if not needs_sponsorship:
        return True, None  # candidate does not need sponsorship - never filtered on this axis

    text = posting.description or ""
    for pattern in NO_SPONSORSHIP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "posting states no sponsorship, and candidate needs sponsorship"

    return True, None


HARD_FILTERS = [check_location, check_seniority, check_sponsorship]


def apply_hard_filters(postings: list[Posting], profile: Profile) -> list[FilterResult]:
    results = []
    for posting in postings:
        reasons = []
        for filter_fn in HARD_FILTERS:
            passed, reason = filter_fn(posting, profile)
            if not passed and reason:
                reasons.append(reason)
        results.append(FilterResult(posting=posting, passed=(len(reasons) == 0), reasons=reasons))
    return results
