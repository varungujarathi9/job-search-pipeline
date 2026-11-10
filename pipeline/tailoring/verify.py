"""Verify every claim in a TailoredOutput traces to the profile.

This is the enforcement point referenced in docs/tailoring.md: an output
with even one untraceable claim is blocked (verify_output returns is_valid
False with the offending claims), and the CLI in pipeline/cli/tailor_verify.py
exits non-zero so a human or an orchestrating command cannot silently ship
blocked output.

Checks performed per claim, depending on source_kind:
  accomplishment  - source_ref must be a real accomplishment id; every
                    number appearing in the claim text must also appear in
                    that accomplishment's title or metrics text (catches a
                    real id cited for a fabricated or altered metric).
  candidate_fact  - source_ref must resolve to a real field in the profile,
                    and the claim text, once normalized, must equal that
                    field's value; for a list field, the text must equal one
                    element, or split (on commas/semicolons/" and ") into one
                    or more segments that each equal an element.
  boilerplate     - claim text must contain no digit and no token matching
                    any accomplishment's skills/tags or any company name
                    from profile.accomplishments (a boilerplate claim is not
                    allowed to smuggle in an unsourced fact).
"""

from __future__ import annotations

import dataclasses
import re

from pipeline.profile import Profile
from pipeline.tailoring.schema import Claim, TailoredOutput

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?%?")


@dataclasses.dataclass
class ClaimViolation:
    claim: Claim
    reason: str


@dataclasses.dataclass
class VerificationResult:
    is_valid: bool
    violations: list[ClaimViolation]


def _numbers_in(text: str) -> set[str]:
    return set(NUMBER_PATTERN.findall(text))


def _resolve_candidate_fact(profile: Profile, field_path: str) -> object | None:
    parts = field_path.split(".")
    node: object = profile.data
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list):
            # allow paths like "education.0.degree"
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return node


def _verify_accomplishment_claim(claim: Claim, profile: Profile) -> str | None:
    if claim.source_ref is None or not profile.has_accomplishment(claim.source_ref):
        return f"source_ref '{claim.source_ref}' is not a known accomplishment id"

    accomplishment = profile.accomplishments_by_id[claim.source_ref]
    source_text = accomplishment.title + " " + " ".join(accomplishment.metrics)
    source_numbers = _numbers_in(source_text)
    claim_numbers = _numbers_in(claim.text)

    unsupported = claim_numbers - source_numbers
    if unsupported:
        return (
            f"claim cites numbers {sorted(unsupported)} not present in "
            f"accomplishment '{claim.source_ref}' (title+metrics)"
        )
    return None


def _normalize(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


SEGMENT_SPLIT_PATTERN = re.compile(r",|;| and ")


def _split_segments(text: str) -> list[str]:
    return [seg.strip() for seg in SEGMENT_SPLIT_PATTERN.split(text) if seg.strip()]


def _verify_candidate_fact_claim(claim: Claim, profile: Profile) -> str | None:
    if claim.source_ref is None:
        return "candidate_fact claim has no source_ref"
    value = _resolve_candidate_fact(profile, claim.source_ref)
    if value is None:
        return f"source_ref '{claim.source_ref}' does not resolve to a profile field"

    claim_text = _normalize(claim.text)
    if isinstance(value, list):
        elements = {_normalize(v) for v in value}
        segments = _split_segments(claim_text)
        if not segments or not all(segment in elements for segment in segments):
            return (
                f"claim text is not a list of values from profile field "
                f"'{claim.source_ref}' ({value!r})"
            )
    else:
        if claim_text != _normalize(value):
            return (
                f"claim text does not equal the value of profile field "
                f"'{claim.source_ref}' ({value!r})"
            )
    return None


def _all_known_fact_tokens(profile: Profile) -> set[str]:
    tokens: set[str] = set()
    for acc in profile.accomplishments_by_id.values():
        for skill in acc.skills:
            tokens.add(skill.lower())
        for tag in acc.tags:
            tokens.add(tag.lower())
        company = acc.raw.get("company")
        if company:
            tokens.add(company.lower())
    return tokens


def _verify_boilerplate_claim(claim: Claim, profile: Profile) -> str | None:
    if _numbers_in(claim.text):
        return "boilerplate claim must not contain a number"

    known_tokens = _all_known_fact_tokens(profile)
    lowered = claim.text.lower()
    for token in known_tokens:
        if token and token in lowered:
            return f"boilerplate claim smuggles in sourced fact token '{token}'"
    return None


_VERIFIERS = {
    "accomplishment": _verify_accomplishment_claim,
    "candidate_fact": _verify_candidate_fact_claim,
    "boilerplate": _verify_boilerplate_claim,
}


def verify_output(output: TailoredOutput, profile: Profile) -> VerificationResult:
    violations: list[ClaimViolation] = []
    for claim in output.claims:
        verifier = _VERIFIERS.get(claim.source_kind)
        if verifier is None:
            violations.append(
                ClaimViolation(claim=claim, reason=f"unknown source_kind '{claim.source_kind}'")
            )
            continue
        reason = verifier(claim, profile)
        if reason:
            violations.append(ClaimViolation(claim=claim, reason=reason))

    return VerificationResult(is_valid=(len(violations) == 0), violations=violations)
