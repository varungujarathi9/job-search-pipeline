"""Types for LLM scoring output. Scoring itself is performed by Claude Code
(see .claude/commands/jsp-daily.md) reading profile.yaml and the filtered
postings this module's dataclass serializes to/from JSON. This module holds
no model calls - the agent is the scorer, this is only its I/O contract.
"""

from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class ScoredPosting:
    dedupe_key: str
    company: str
    title: str
    location: str
    url: str
    score: int  # 0-100
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ScoredPosting":
        return ScoredPosting(
            dedupe_key=data["dedupe_key"],
            company=data["company"],
            title=data["title"],
            location=data["location"],
            url=data["url"],
            score=int(data["score"]),
            rationale=data["rationale"],
        )


def top_n(scored: list[ScoredPosting], n: int = 10) -> list[ScoredPosting]:
    return sorted(scored, key=lambda s: s.score, reverse=True)[:n]
