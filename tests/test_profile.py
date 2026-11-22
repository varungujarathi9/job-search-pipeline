import unittest
from pathlib import Path

import yaml

from pipeline.profile import validate_profile

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PROFILE_PATH = REPO_ROOT / "profile" / "profile.example.yaml"


def _load_example_profile():
    with EXAMPLE_PROFILE_PATH.open("r", encoding="utf-8") as f:
        return validate_profile(yaml.safe_load(f))


class TestStandardAnswers(unittest.TestCase):
    def test_example_profile_has_required_field_answers(self):
        profile = _load_example_profile()
        answers = profile.standard_answers

        self.assertIn("work_authorized_us", answers)
        self.assertIn("age_18_or_older", answers)
        self.assertIsInstance(answers["work_authorized_us"], bool)
        self.assertIsInstance(answers["age_18_or_older"], bool)

    def test_standard_answers_defaults_to_empty_dict_when_absent(self):
        data = {
            "candidate": {"name": "Test Candidate"},
            "target": {},
            "visa": {"needs_sponsorship": False},
            "dealbreakers": [],
            "accomplishments": [
                {"id": "acc-001", "title": "Did a thing", "metrics": [], "skills": [], "tags": []}
            ],
        }
        profile = validate_profile(data)
        self.assertEqual(profile.standard_answers, {})


if __name__ == "__main__":
    unittest.main()
