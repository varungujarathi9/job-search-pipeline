"""Fetch postings from a company's public Ashby job board API.

API docs: https://developers.ashbyhq.com/reference/jobboardwithteams
Endpoint: https://api.ashbyhq.com/posting-api/job-board/{board_name}
"""

from __future__ import annotations

from typing import Any

import requests

from pipeline.postings import Posting

ASHBY_API_URL = "https://api.ashbyhq.com/posting-api/job-board/{board_token}"


def fetch_ashby_postings(
    company_name: str, board_token: str, *, timeout: int = 20
) -> list[Posting]:
    url = ASHBY_API_URL.format(board_token=board_token)
    response = requests.get(url, params={"includeCompensation": "true"}, timeout=timeout)
    response.raise_for_status()
    return parse_ashby_response(response.json(), company_name, board_token)


def parse_ashby_response(
    payload: dict[str, Any], company_name: str, board_token: str
) -> list[Posting]:
    postings = []
    for job in payload.get("jobs", []):
        postings.append(
            Posting(
                source="ashby",
                company=company_name,
                board_token=board_token,
                external_id=str(job["id"]),
                title=job.get("title", ""),
                location=job.get("location", ""),
                url=job.get("jobUrl", ""),
                description=job.get("descriptionPlain", "") or job.get("descriptionHtml", "") or "",
                posted_at=job.get("publishedAt"),
                raw=job,
            )
        )
    return postings
