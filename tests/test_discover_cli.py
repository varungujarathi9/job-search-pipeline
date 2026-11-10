import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from pipeline.cli import discover

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "fixtures" / "feeds"
EXAMPLE_PROFILE = REPO_ROOT / "profile" / "profile.example.yaml"


def _fixture_response(name: str):
    with (FIXTURES / name).open("r", encoding="utf-8") as f:
        payload = json.load(f)
    mock_response = mock.Mock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status.return_value = None
    return mock_response


class TestDiscoverCli(unittest.TestCase):
    def test_end_to_end_with_fixture_feeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            companies_path = tmp_path / "companies.yaml"
            companies_path.write_text(
                yaml.dump(
                    {
                        "companies": [
                            {"name": "Example Robotics", "ats": "greenhouse", "board_token": "examplerobotics"},
                            {"name": "Example Climate", "ats": "lever", "board_token": "exampleclimate"},
                            {"name": "Example Devtools", "ats": "ashby", "board_token": "exampledevtools"},
                        ]
                    }
                )
            )
            output_path = tmp_path / "filtered_postings.json"

            responses = {
                "https://boards-api.greenhouse.io/v1/boards/examplerobotics/jobs": _fixture_response(
                    "greenhouse_examplerobotics.json"
                ),
                "https://api.lever.co/v0/postings/exampleclimate": _fixture_response(
                    "lever_exampleclimate.json"
                ),
                "https://api.ashbyhq.com/posting-api/job-board/exampledevtools": _fixture_response(
                    "ashby_exampledevtools.json"
                ),
            }

            def fake_get(url, params=None, timeout=None):
                return responses[url]

            with mock.patch("requests.get", side_effect=fake_get):
                exit_code = discover.main(
                    [
                        "--companies",
                        str(companies_path),
                        "--profile",
                        str(EXAMPLE_PROFILE),
                        "--output",
                        str(output_path),
                        "--no-save-seen",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            with output_path.open("r", encoding="utf-8") as f:
                filtered = json.load(f)

            titles = {p["title"] for p in filtered}
            # Junior role and SF-onsite Director role must be hard-filtered out.
            self.assertNotIn("Junior Backend Engineer", titles)
            self.assertNotIn("Director of Engineering", titles)
            # Matching senior/staff roles should survive.
            self.assertIn("Senior Backend Engineer", titles)
            self.assertGreaterEqual(len(filtered), 3)


if __name__ == "__main__":
    unittest.main()
