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
    company: str | None
    role: str | None
    start_date: str | None
    end_date: str | None
    is_project: bool
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

    @property
    def skills(self) -> dict[str, list[str]]:
        return self.data.get("skills", {}) or {}

    @property
    def education(self) -> list[dict[str, Any]]:
        return self.data.get("education", []) or []

    @property
    def role_accomplishments(self) -> list[Accomplishment]:
        return [a for a in self.accomplishments_by_id.values() if not a.is_project]

    @property
    def projects(self) -> list[Accomplishment]:
        return [a for a in self.accomplishments_by_id.values() if a.is_project]


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

    projects_raw = data.get("projects", []) or []
    if not isinstance(projects_raw, list):
        raise ProfileError("Profile 'projects', if present, must be a list.")

    seen_ids: set[str] = set()
    accomplishments_by_id: dict[str, Accomplishment] = {}
    for entry, is_project in [(e, False) for e in accomplishments_raw] + [
        (e, True) for e in projects_raw
    ]:
        if "id" not in entry:
            kind = "project" if is_project else "accomplishment"
            raise ProfileError(f"{kind.capitalize()} missing 'id': {entry!r}")
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
            company=entry.get("company"),
            role=entry.get("role"),
            start_date=entry.get("start_date"),
            end_date=entry.get("end_date"),
            is_project=is_project,
            raw=entry,
        )

    return Profile(data=data, accomplishments_by_id=accomplishments_by_id)
