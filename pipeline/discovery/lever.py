"""Fetch postings from a company's public Lever job board API.

API docs: https://github.com/lever/postings-api
Endpoint: https://api.lever.co/v0/postings/{company}?mode=json
"""

from __future__ import annotations

from typing import Any

import requests

from pipeline.postings import Posting

LEVER_API_URL = "https://api.lever.co/v0/postings/{board_token}"


def fetch_lever_postings(
    company_name: str, board_token: str, *, timeout: int = 20
) -> list[Posting]:
    url = LEVER_API_URL.format(board_token=board_token)
    response = requests.get(url, params={"mode": "json"}, timeout=timeout)
    response.raise_for_status()
    return parse_lever_response(response.json(), company_name, board_token)


def parse_lever_response(
    payload: list[dict[str, Any]], company_name: str, board_token: str
) -> list[Posting]:
    postings = []
    for job in payload:
        categories = job.get("categories", {}) or {}
        postings.append(
            Posting(
                source="lever",
                company=company_name,
                board_token=board_token,
                external_id=str(job["id"]),
                title=job.get("text", ""),
                location=categories.get("location", ""),
                url=job.get("hostedUrl", ""),
                description=job.get("descriptionPlain", "") or job.get("description", "") or "",
                posted_at=_epoch_ms_to_iso(job.get("createdAt")),
                raw=job,
            )
        )
    return postings


def _epoch_ms_to_iso(epoch_ms: int | None) -> str | None:
    if epoch_ms is None:
        return None
    import datetime

    return datetime.datetime.fromtimestamp(epoch_ms / 1000, tz=datetime.timezone.utc).isoformat()
