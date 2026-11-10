import unittest
from pathlib import Path

import yaml

from pipeline.hard_filters import apply_hard_filters
from pipeline.postings import Posting
from pipeline.profile import validate_profile

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PROFILE_PATH = REPO_ROOT / "profile" / "profile.example.yaml"


def _load_example_profile():
    with EXAMPLE_PROFILE_PATH.open("r", encoding="utf-8") as f:
        return validate_profile(yaml.safe_load(f))


def _posting(**overrides) -> Posting:
    defaults = dict(
        source="greenhouse",
        company="Example Co",
        board_token="examplecorp",
        external_id="1",
        title="Senior Backend Engineer",
        location="Denver, CO",
        url="https://example.com/job/1",
        description="",
        posted_at=None,
    )
    defaults.update(overrides)
    return Posting(**defaults)


class TestHardFilters(unittest.TestCase):
    def setUp(self):
        self.profile = _load_example_profile()

    def test_matching_posting_passes_all_filters(self):
        posting = _posting(title="Senior Backend Engineer", location="Denver, CO")
        [result] = apply_hard_filters([posting], self.profile)
        self.assertTrue(result.passed, result.reasons)

    def test_junior_title_filtered_out(self):
        posting = _posting(title="Junior Backend Engineer", location="Denver, CO")
        [result] = apply_hard_filters([posting], self.profile)
        self.assertFalse(result.passed)
        self.assertTrue(any("seniority" in r for r in result.reasons))

    def test_trailing_roman_numeral_i_title_filtered_out(self):
        posting = _posting(title="Backend Engineer I", location="Denver, CO")
        [result] = apply_hard_filters([posting], self.profile)
        self.assertFalse(result.passed)
        self.assertTrue(any("seniority" in r for r in result.reasons))

    def test_standalone_word_i_in_title_is_not_misclassified_as_junior(self):
        posting = _posting(title="Backend Engineer - I lead a small team", location="Denver, CO")
        [result] = apply_hard_filters([posting], self.profile)
        self.assertTrue(result.passed, result.reasons)

    def test_director_title_filtered_out(self):
        posting = _posting(title="Director of Engineering", location="Denver, CO")
        [result] = apply_hard_filters([posting], self.profile)
        self.assertFalse(result.passed)
        self.assertTrue(any("seniority" in r for r in result.reasons))

    def test_onsite_non_target_location_filtered_out(self):
        posting = _posting(title="Senior Backend Engineer", location="San Francisco, CA")
        [result] = apply_hard_filters([posting], self.profile)
        self.assertFalse(result.passed)
        self.assertTrue(any("location" in r for r in result.reasons))

    def test_remote_allowed_when_remote_ok(self):
        # example profile has remote_ok: true
        posting = _posting(title="Senior Backend Engineer", location="Remote - US")
        [result] = apply_hard_filters([posting], self.profile)
        self.assertTrue(result.passed, result.reasons)

    def test_sponsorship_not_filtered_when_candidate_does_not_need_it(self):
        # example profile: needs_sponsorship: false
        posting = _posting(
            title="Senior Backend Engineer",
            location="Denver, CO",
            description="No visa sponsorship available for this role.",
        )
        [result] = apply_hard_filters([posting], self.profile)
        self.assertTrue(result.passed, result.reasons)

    def test_sponsorship_filtered_when_candidate_needs_it_and_none_offered(self):
        profile = self.profile
        profile.data["visa"]["needs_sponsorship"] = True
        posting = _posting(
            title="Senior Backend Engineer",
            location="Denver, CO",
            description="No visa sponsorship available for this role.",
        )
        [result] = apply_hard_filters([posting], profile)
        self.assertFalse(result.passed)
        self.assertTrue(any("sponsorship" in r for r in result.reasons))


if __name__ == "__main__":
    unittest.main()
