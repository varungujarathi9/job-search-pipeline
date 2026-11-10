"""Load and validate the candidate profile (profile/profile.yaml)."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE_PATH = REPO_ROOT / "profile" / "profile.yaml"
EXAMPLE_PROFILE_PATH = REPO_ROOT / "profile" / "profile.example.yaml"

REQUIRED_TOP_LEVEL_KEYS = (
    "candidate",
    "target",
    "visa",
    "dealbreakers",
    "accomplishments",
)


class ProfileError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class Accomplishment:
    id: str
    title: str
    metrics: list[str]
    skills: list[str]
    tags: list[str]
    raw: dict[str, Any]


@dataclasses.dataclass(frozen=True)
class Profile:
    data: dict[str, Any]
    accomplishments_by_id: dict[str, Accomplishment]

    @property
    def target(self) -> dict[str, Any]:
        return self.data["target"]

    @property
    def visa(self) -> dict[str, Any]:
        return self.data["visa"]

    @property
    def dealbreakers(self) -> list[str]:
        return self.data.get("dealbreakers", [])

    def has_accomplishment(self, accomplishment_id: str) -> bool:
        return accomplishment_id in self.accomplishments_by_id


def load_profile(path: Path | None = None) -> Profile:
    """Load profile.yaml. Raises ProfileError if missing or malformed."""
    profile_path = path or DEFAULT_PROFILE_PATH
    if not profile_path.exists():
        raise ProfileError(
            f"Profile not found at {profile_path}. "
            f"Copy {EXAMPLE_PROFILE_PATH.name} to {profile_path.name} and fill in your facts."
        )

    with profile_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return validate_profile(data)


def validate_profile(data: dict[str, Any]) -> Profile:
    if not isinstance(data, dict):
        raise ProfileError("Profile file must contain a YAML mapping at the top level.")

    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in data]
    if missing:
        raise ProfileError(f"Profile is missing required keys: {missing}")

    accomplishments_raw = data.get("accomplishments", [])
    if not isinstance(accomplishments_raw, list) or not accomplishments_raw:
        raise ProfileError("Profile must include a non-empty 'accomplishments' list.")

    seen_ids: set[str] = set()
    accomplishments_by_id: dict[str, Accomplishment] = {}
    for entry in accomplishments_raw:
        if "id" not in entry:
            raise ProfileError(f"Accomplishment missing 'id': {entry!r}")
        acc_id = entry["id"]
        if acc_id in seen_ids:
            raise ProfileError(f"Duplicate accomplishment id: {acc_id}")
        seen_ids.add(acc_id)
        accomplishments_by_id[acc_id] = Accomplishment(
            id=acc_id,
            title=entry.get("title", ""),
            metrics=entry.get("metrics", []),
            skills=entry.get("skills", []),
            tags=entry.get("tags", []),
            raw=entry,
        )

    return Profile(data=data, accomplishments_by_id=accomplishments_by_id)
