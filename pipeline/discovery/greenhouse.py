"""Fetch postings from a company's public Greenhouse job board API.

API docs: https://developers.greenhouse.io/job-board.html
Endpoint: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
"""

from __future__ import annotations

from typing import Any

import requests

from pipeline.postings import Posting

GREENHOUSE_API_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


def fetch_greenhouse_postings(
    company_name: str, board_token: str, *, timeout: int = 20
) -> list[Posting]:
    url = GREENHOUSE_API_URL.format(board_token=board_token)
    response = requests.get(url, params={"content": "true"}, timeout=timeout)
    response.raise_for_status()
    return parse_greenhouse_response(response.json(), company_name, board_token)


def parse_greenhouse_response(
    payload: dict[str, Any], company_name: str, board_token: str
) -> list[Posting]:
    postings = []
    for job in payload.get("jobs", []):
        location = (job.get("location") or {}).get("name", "")
        postings.append(
            Posting(
                source="greenhouse",
                company=company_name,
                board_token=board_token,
                external_id=str(job["id"]),
                title=job.get("title", ""),
                location=location,
                url=job.get("absolute_url", ""),
                description=job.get("content", "") or "",
                posted_at=job.get("updated_at"),
                raw=job,
            )
        )
    return postings
