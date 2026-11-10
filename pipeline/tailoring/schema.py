"""Schema for tailored resume/answer output.

Every claim in a generated resume variant or short answer must cite the
profile fact it comes from, so verify.py can check that fact actually exists
before the output is allowed to reach the user. See docs/tailoring.md.

Allowed source kinds:
  "accomplishment" - cites an accomplishments[].id from the profile.
  "candidate_fact"  - cites a literal field path into profile.candidate
                       (e.g. "candidate.email") or profile.education.
  "boilerplate"     - a claim-free connective phrase with no factual content
                       (e.g. "I'm excited to apply"). Must not contain any
                       number, date, employer name, or skill name.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Literal

SourceKind = Literal["accomplishment", "candidate_fact", "boilerplate"]


@dataclasses.dataclass
class Claim:
    text: str
    source_kind: SourceKind
    source_ref: str | None  # accomplishment id, or a field path, or None for boilerplate

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Claim":
        return Claim(
            text=data["text"],
            source_kind=data["source_kind"],
            source_ref=data.get("source_ref"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "source_kind": self.source_kind, "source_ref": self.source_ref}


@dataclasses.dataclass
class TailoredOutput:
    target_company: str
    target_role: str
    claims: list[Claim]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "TailoredOutput":
        return TailoredOutput(
            target_company=data["target_company"],
            target_role=data["target_role"],
            claims=[Claim.from_dict(c) for c in data["claims"]],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_company": self.target_company,
            "target_role": self.target_role,
            "claims": [c.to_dict() for c in self.claims],
        }
