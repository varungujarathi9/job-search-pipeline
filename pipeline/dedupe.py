"""Dedupe postings against previously-seen postings.

Seen postings are tracked by dedupe_key in a gitignored JSON store under
data/seen_postings.json so re-polling the same feed daily does not resurface
postings already scored on a prior day.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.postings import Posting

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEEN_STORE_PATH = REPO_ROOT / "data" / "seen_postings.json"


def load_seen_keys(path: Path | None = None) -> set[str]:
    store_path = path or DEFAULT_SEEN_STORE_PATH
    if not store_path.exists():
        return set()
    with store_path.open("r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen_keys(keys: set[str], path: Path | None = None) -> None:
    store_path = path or DEFAULT_SEEN_STORE_PATH
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("w", encoding="utf-8") as f:
        json.dump(sorted(keys), f, indent=2)


def dedupe_postings(
    postings: list[Posting], seen_keys: set[str]
) -> tuple[list[Posting], set[str]]:
    """Return (new_postings, updated_seen_keys).

    Also dedupes within a single batch: if the same dedupe_key appears twice
    in `postings` (e.g. two companies' boards listing the same posting id
    coincidentally, or a feed returning a job twice), only the first is kept.
    """
    new_postings: list[Posting] = []
    updated_keys = set(seen_keys)
    batch_keys_used: set[str] = set()

    for posting in postings:
        key = posting.dedupe_key
        if key in updated_keys or key in batch_keys_used:
            continue
        new_postings.append(posting)
        batch_keys_used.add(key)

    updated_keys |= batch_keys_used
    return new_postings, updated_keys
