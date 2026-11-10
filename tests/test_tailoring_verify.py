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
