"""Shared posting data model used across discovery, dedupe, and scoring."""

from __future__ import annotations

import dataclasses
import hashlib
from typing import Any


@dataclasses.dataclass
class Posting:
    source: str  # "greenhouse" | "lever" | "ashby"
    company: str
    board_token: str
    external_id: str
    title: str
    location: str
    url: str
    description: str
    posted_at: str | None  # ISO 8601 string, may be None if the ATS omits it
    raw: dict[str, Any] = dataclasses.field(default_factory=dict, repr=False)

    @property
    def dedupe_key(self) -> str:
        """Stable key for identifying the same posting across polls.

        Postings are keyed by (source, board_token, external_id) rather than
        title/company text, since the ATS-assigned id is stable across edits
        to the posting while free text is not.
        """
        raw_key = f"{self.source}:{self.board_token}:{self.external_id}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "company": self.company,
            "board_token": self.board_token,
            "external_id": self.external_id,
            "title": self.title,
            "location": self.location,
            "url": self.url,
            "description": self.description,
            "posted_at": self.posted_at,
            "dedupe_key": self.dedupe_key,
        }
