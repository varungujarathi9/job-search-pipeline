"""Discovery: poll Greenhouse, Lever, and Ashby public job board feeds."""

from pipeline.discovery.ashby import fetch_ashby_postings
from pipeline.discovery.greenhouse import fetch_greenhouse_postings
from pipeline.discovery.lever import fetch_lever_postings

FETCHERS = {
    "greenhouse": fetch_greenhouse_postings,
    "lever": fetch_lever_postings,
    "ashby": fetch_ashby_postings,
}

__all__ = ["FETCHERS", "fetch_greenhouse_postings", "fetch_lever_postings", "fetch_ashby_postings"]
