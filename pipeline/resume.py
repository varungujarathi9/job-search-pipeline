"""Build a one-page resume layout from a verified TailoredOutput.

This module only arranges and selects text that already exists in
profile/profile.yaml or in a TailoredOutput's claims - both of which have
already passed pipeline/tailoring/verify.py by the time render_resume.py
calls into this module. It introduces no new facts: every bullet is either a
verified claim's text or an accomplishment's own title/metrics text, and
every other field is read directly off the profile.

Layout produced (see docs/tailoring.md for the full contract):
  - Contact line: candidate name, email, phone, location, links.
  - Experience: accomplishments grouped by (company, role), roles ordered
    most-recent-first by start_date, bullets within a role ordered by the
    verified draft's relevance order (the order claims appear in the
    draft), using the draft's claim text where a claim cites that
    accomplishment id and falling back to the accomplishment's own title
    and metrics otherwise.
  - Skills: reordered so any group with a value mentioned in the draft's
    claim text comes first; original group order otherwise.
  - Education, Projects: rendered as-is from the profile.
"""

from __future__ import annotations

import dataclasses
import re

from pipeline.profile import Accomplishment, Profile
from pipeline.tailoring.schema import TailoredOutput

_SKILL_GROUP_ORDER = ("languages", "frameworks_tools", "cloud")


@dataclasses.dataclass
class RoleSection:
    company: str
    role: str
    start_date: str | None
    end_date: str | None
    bullets: list[str]


@dataclasses.dataclass
class ResumeLayout:
    candidate_name: str
    contact_line: str
    role_sections: list[RoleSection]
    skill_groups: list[tuple[str, list[str]]]  # (group_label, values), ordered
    education: list[dict[str, object]]
    projects: list[tuple[str, list[str]]]  # (project title, bullet lines)


def _bullet_text_for(accomplishment: Accomplishment, claim_text_by_acc_id: dict[str, str]) -> str:
    if accomplishment.id in claim_text_by_acc_id:
        return claim_text_by_acc_id[accomplishment.id]
    if accomplishment.metrics:
        return f"{accomplishment.title} - {'; '.join(accomplishment.metrics)}"
    return accomplishment.title


def _sort_key_start_date(value: str | None) -> str:
    # Missing start_date sorts as oldest so dated roles still order correctly.
    return value or ""


def _build_role_sections(
    profile: Profile, claim_order_by_acc_id: dict[str, int], claim_text_by_acc_id: dict[str, str]
) -> list[RoleSection]:
    groups: dict[tuple[str, str], list[Accomplishment]] = {}
    group_order: list[tuple[str, str]] = []
    for acc in profile.role_accomplishments:
        key = (acc.company or "", acc.role or "")
        if key not in groups:
            groups[key] = []
            group_order.append(key)
        groups[key].append(acc)

    def role_sort_key(key: tuple[str, str]) -> tuple[str, int]:
        accs = groups[key]
        latest_start = max((a.start_date or "" for a in accs), default="")
        # Reverse-chronological: most recent start_date first.
        return (latest_start,)

    ordered_keys = sorted(group_order, key=role_sort_key, reverse=True)

    sections: list[RoleSection] = []
    for company, role in ordered_keys:
        accs = groups[(company, role)]

        def bullet_sort_key(acc: Accomplishment) -> tuple[int, int]:
            if acc.id in claim_order_by_acc_id:
                return (0, claim_order_by_acc_id[acc.id])
            return (1, group_order.index((company, role)))

        ordered_accs = sorted(accs, key=bullet_sort_key)
        start_date = min((a.start_date for a in accs if a.start_date), default=None)
        end_date = max((a.end_date for a in accs if a.end_date), default=None)
        sections.append(
            RoleSection(
                company=company,
                role=role,
                start_date=start_date,
                end_date=end_date,
                bullets=[_bullet_text_for(acc, claim_text_by_acc_id) for acc in ordered_accs],
            )
        )
    return sections


def _build_skill_groups(profile: Profile, all_claim_text: str) -> list[tuple[str, list[str]]]:
    skills = profile.skills
    lowered_text = all_claim_text.lower()

    def group_mentioned(values: list[str]) -> bool:
        return any(
            re.search(rf"\b{re.escape(v.lower())}\b", lowered_text) for v in values
        )

    groups = [(label, skills[label]) for label in _SKILL_GROUP_ORDER if skills.get(label)]
    # Preserve relative order within "mentioned" and "not mentioned" buckets.
    mentioned = [g for g in groups if group_mentioned(g[1])]
    not_mentioned = [g for g in groups if not group_mentioned(g[1])]
    return mentioned + not_mentioned


def _build_projects(
    profile: Profile, claim_text_by_acc_id: dict[str, str]
) -> list[tuple[str, list[str]]]:
    result = []
    for proj in profile.projects:
        bullet = _bullet_text_for(proj, claim_text_by_acc_id)
        result.append((proj.title, [bullet]))
    return result


def build_layout(output: TailoredOutput, profile: Profile) -> ResumeLayout:
    """Assemble a ResumeLayout from a verified TailoredOutput and the profile.

    Caller must have already run this output through
    pipeline.tailoring.verify.verify_output and confirmed is_valid - this
    function does not re-check claims, it only arranges already-verified
    text and literal profile fields.
    """
    claim_order_by_acc_id: dict[str, int] = {}
    claim_text_by_acc_id: dict[str, str] = {}
    for index, claim in enumerate(output.claims):
        if claim.source_kind == "accomplishment" and claim.source_ref is not None:
            if claim.source_ref not in claim_order_by_acc_id:
                claim_order_by_acc_id[claim.source_ref] = index
            claim_text_by_acc_id[claim.source_ref] = claim.text

    all_claim_text = " ".join(c.text for c in output.claims)

    candidate = profile.data.get("candidate", {})
    name = candidate.get("name", "")
    contact_parts = [
        p
        for p in [
            candidate.get("email"),
            candidate.get("phone"),
            candidate.get("location"),
        ]
        if p
    ]
    links = candidate.get("links", {}) or {}
    contact_parts.extend([v for v in links.values() if v])
    contact_line = " | ".join(contact_parts)

    return ResumeLayout(
        candidate_name=name,
        contact_line=contact_line,
        role_sections=_build_role_sections(profile, claim_order_by_acc_id, claim_text_by_acc_id),
        skill_groups=_build_skill_groups(profile, all_claim_text),
        education=list(profile.education),
        projects=_build_projects(profile, claim_text_by_acc_id),
    )
