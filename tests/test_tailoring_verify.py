import unittest
from pathlib import Path

import yaml

from pipeline.profile import validate_profile
from pipeline.tailoring.schema import Claim, TailoredOutput
from pipeline.tailoring.verify import verify_output

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PROFILE_PATH = REPO_ROOT / "profile" / "profile.example.yaml"


def _load_example_profile():
    with EXAMPLE_PROFILE_PATH.open("r", encoding="utf-8") as f:
        return validate_profile(yaml.safe_load(f))


class TestTailoringVerify(unittest.TestCase):
    def setUp(self):
        self.profile = _load_example_profile()

    def test_valid_output_passes(self):
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(
                    text="Reduced billing reconciliation latency from 24h to 15m",
                    source_kind="accomplishment",
                    source_ref="acc-001",
                ),
                Claim(text="Jordan Rivers", source_kind="candidate_fact", source_ref="candidate.name"),
                Claim(text="I'm excited to apply for this role.", source_kind="boilerplate", source_ref=None),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertTrue(result.is_valid, result.violations)

    def test_unknown_accomplishment_id_is_blocked(self):
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(text="Did something great", source_kind="accomplishment", source_ref="acc-999"),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("not a known accomplishment id", result.violations[0].reason)

    def test_fabricated_metric_under_real_id_is_blocked(self):
        # acc-001's real metric is "Reduced... from 24h to 15m" / "Cut... by 32%".
        # Inflating 32% to 90% under the same real id must still be caught.
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(
                    text="Cut infra cost for billing stack by 90%",
                    source_kind="accomplishment",
                    source_ref="acc-001",
                ),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("not present in", result.violations[0].reason)

    def test_unknown_candidate_fact_field_is_blocked(self):
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(text="Has a PhD", source_kind="candidate_fact", source_ref="candidate.phd"),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("does not resolve", result.violations[0].reason)

    def test_fabricated_candidate_fact_text_is_blocked(self):
        # candidate.name resolves to "Jordan Rivers", but the claim text is
        # fabricated and shares no content with that field's value.
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(
                    text="Won a Nobel Prize in Physics",
                    source_kind="candidate_fact",
                    source_ref="candidate.name",
                ),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("does not equal the value", result.violations[0].reason)

    def test_padded_scalar_candidate_fact_is_blocked(self):
        # candidate.name resolves to "Jordan Rivers" exactly; padding a real
        # value with extra fabricated words must still be blocked.
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(
                    text="Jordan Rivers, PhD in astrophysics",
                    source_kind="candidate_fact",
                    source_ref="candidate.name",
                ),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("does not equal the value", result.violations[0].reason)

    def test_padded_list_candidate_fact_is_blocked(self):
        # target.roles is a list of real role titles; appending a fabricated
        # segment alongside a real one must still be blocked.
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(
                    text="Senior Backend Engineer with 20 years at NASA and a PhD in astrophysics",
                    source_kind="candidate_fact",
                    source_ref="target.roles",
                ),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("is not a list of values", result.violations[0].reason)

    def test_bare_scalar_candidate_fact_passes(self):
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(text="Jordan Rivers", source_kind="candidate_fact", source_ref="candidate.name"),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertTrue(result.is_valid, result.violations)

    def test_list_of_real_elements_candidate_fact_passes(self):
        # target.roles in profile.example.yaml includes "Senior Backend
        # Engineer" and "Staff Software Engineer"; citing both, joined with
        # "and", must pass since each segment is a real list element.
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(
                    text="Senior Backend Engineer and Staff Software Engineer",
                    source_kind="candidate_fact",
                    source_ref="target.roles",
                ),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertTrue(result.is_valid, result.violations)

    def test_boilerplate_with_number_is_blocked(self):
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(text="I have 10 years of experience", source_kind="boilerplate", source_ref=None),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("must not contain a number", result.violations[0].reason)

    def test_boilerplate_smuggling_sourced_skill_is_blocked(self):
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(
                    text="I'm particularly excited about using Kafka here",
                    source_kind="boilerplate",
                    source_ref=None,
                ),
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("smuggles in sourced fact token", result.violations[0].reason)

    def test_unknown_source_kind_is_blocked(self):
        output = TailoredOutput(
            target_company="Acme",
            target_role="Senior Backend Engineer",
            claims=[
                Claim(text="Something", source_kind="invented_kind", source_ref=None),  # type: ignore[arg-type]
            ],
        )
        result = verify_output(output, self.profile)
        self.assertFalse(result.is_valid)
        self.assertIn("unknown source_kind", result.violations[0].reason)


if __name__ == "__main__":
    unittest.main()
