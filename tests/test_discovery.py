import json
import unittest
from pathlib import Path

from pipeline.discovery.ashby import parse_ashby_response
from pipeline.discovery.greenhouse import parse_greenhouse_response
from pipeline.discovery.lever import parse_lever_response

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "feeds"


def _load(name: str):
    with (FIXTURES / name).open("r", encoding="utf-8") as f:
        return json.load(f)


class TestGreenhouseParser(unittest.TestCase):
    def test_parses_all_jobs(self):
        payload = _load("greenhouse_examplerobotics.json")
        postings = parse_greenhouse_response(payload, "Example Robotics", "examplerobotics")
        self.assertEqual(len(postings), 3)
        self.assertEqual(postings[0].source, "greenhouse")
        self.assertEqual(postings[0].company, "Example Robotics")
        self.assertEqual(postings[0].title, "Senior Backend Engineer")
        self.assertEqual(postings[0].location, "Denver, CO")
        self.assertIn("No visa sponsorship", postings[0].description)

    def test_same_external_id_across_polls_has_same_dedupe_key(self):
        day1 = parse_greenhouse_response(
            _load("greenhouse_examplerobotics.json"), "Example Robotics", "examplerobotics"
        )
        day2 = parse_greenhouse_response(
            _load("greenhouse_examplerobotics_day2.json"), "Example Robotics", "examplerobotics"
        )
        day1_keys = {p.dedupe_key for p in day1}
        day2_keys = {p.dedupe_key for p in day2}
        overlap = day1_keys & day2_keys
        self.assertEqual(len(overlap), 1, "job 4000001 reappears on day 2 and must dedupe")


class TestLeverParser(unittest.TestCase):
    def test_parses_all_jobs(self):
        payload = _load("lever_exampleclimate.json")
        postings = parse_lever_response(payload, "Example Climate", "exampleclimate")
        self.assertEqual(len(postings), 3)
        self.assertEqual(postings[0].source, "lever")
        self.assertEqual(postings[1].title, "Engineering Manager, Platform")
        self.assertEqual(postings[2].location, "San Francisco, CA")

    def test_created_at_converted_to_iso(self):
        payload = _load("lever_exampleclimate.json")
        postings = parse_lever_response(payload, "Example Climate", "exampleclimate")
        self.assertIsNotNone(postings[0].posted_at)
        self.assertIn("2025", postings[0].posted_at)


class TestAshbyParser(unittest.TestCase):
    def test_parses_all_jobs(self):
        payload = _load("ashby_exampledevtools.json")
        postings = parse_ashby_response(payload, "Example Devtools", "exampledevtools")
        self.assertEqual(len(postings), 2)
        self.assertEqual(postings[0].source, "ashby")
        self.assertEqual(postings[0].title, "Staff Software Engineer")
        self.assertEqual(postings[1].location, "Denver, CO")


if __name__ == "__main__":
    unittest.main()
