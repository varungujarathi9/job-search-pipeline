import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from pipeline.profile import validate_profile
from pipeline.resume import build_layout
from pipeline.tailoring.schema import Claim, TailoredOutput
from pipeline.tailoring.verify import verify_output

REPO_ROOT = Path(__file__).resolve().parent.parent

_FICTIONAL_PROFILE_YAML = """
candidate:
  name: "Fictional Candidate"
  legal_first_name: "Fictionalia"
  legal_last_name: "Candidatesson"
  email: "fictional.candidate@example.com"
  phone: "+1-555-000-0000"
  location: "Nowhere, NA"
  links:
    linkedin: "https://www.linkedin.com/in/fictional-example"

target:
  roles: ["Fictional Engineer"]
  seniority_min: "senior"
  seniority_max: "staff"
  locations: ["Remote - US"]
  remote_ok: true
  relocation_ok: false

visa:
  needs_sponsorship: false
  work_authorization: "US Citizen"

dealbreakers: []

skills:
  languages: ["Pythonic", "Gofer"]
  frameworks_tools: ["Fakeframework"]
  cloud: ["FakeCloud"]

accomplishments:
  - id: acc-f1
    title: "Did a fictional thing"
    company: "Fictional Corp"
    role: "Fictional Engineer"
    start_date: "2022-01"
    end_date: "2024-01"
    metrics:
      - "Improved fictional metric by 42%"
    skills: ["Pythonic"]
    tags: ["fictional"]
  - id: acc-f2
    title: "Did an earlier fictional thing"
    company: "Older Fictional Inc"
    role: "Junior Fictional Engineer"
    start_date: "2019-01"
    end_date: "2021-12"
    metrics:
      - "Shipped 3 fictional widgets"
    skills: ["Gofer"]
    tags: ["fictional"]

education:
  - degree: "B.S. Fictional Studies"
    school: "Fictional State University"
    graduation_year: 2018

projects:
  - id: proj-f1
    title: "Fictional side project"
    metrics:
      - "100 fictional users"
    skills: ["Pythonic"]
    tags: ["fictional"]

standard_answers:
  why_interested_template: "I'm drawn to {company}."
  work_authorization_statement: "I am a US Citizen."
"""


def _load_fictional_profile():
    return validate_profile(yaml.safe_load(_FICTIONAL_PROFILE_YAML))


def _valid_output() -> TailoredOutput:
    return TailoredOutput(
        target_company="Fictional Target Co",
        target_role="Fictional Engineer",
        claims=[
            Claim(
                text="Improved fictional metric by 42%",
                source_kind="accomplishment",
                source_ref="acc-f1",
            ),
            Claim(text="Fictional Candidate", source_kind="candidate_fact", source_ref="candidate.name"),
            Claim(
                text="I'm excited to apply for this role.",
                source_kind="boilerplate",
                source_ref=None,
            ),
        ],
    )


class TestResumeLayout(unittest.TestCase):
    def setUp(self):
        self.profile = _load_fictional_profile()

    def test_layout_contains_only_profile_facts(self):
        output = _valid_output()
        result = verify_output(output, self.profile)
        self.assertTrue(result.is_valid, result.violations)

        layout = build_layout(output, self.profile)

        self.assertEqual(layout.candidate_name, "Fictional Candidate")
        self.assertIn("fictional.candidate@example.com", layout.contact_line)

        all_bullets = [b for section in layout.role_sections for b in section.bullets]
        # The claim-cited accomplishment must use the verified claim text.
        self.assertIn("Improved fictional metric by 42%", all_bullets)
        # The non-cited accomplishment must fall back to its own profile text,
        # not an invented bullet.
        joined = " ".join(all_bullets)
        self.assertIn("Shipped 3 fictional widgets", joined)

        # No fabricated content: every bullet must trace to either the claim
        # text or an accomplishment's own title/metrics text.
        known_strings = {c.text for c in output.claims}
        for acc in self.profile.role_accomplishments:
            known_strings.add(f"{acc.title} - {'; '.join(acc.metrics)}")
            known_strings.add(acc.title)
        for bullet in all_bullets:
            self.assertIn(bullet, known_strings)

    def test_roles_ordered_reverse_chronologically(self):
        output = _valid_output()
        layout = build_layout(output, self.profile)
        companies = [s.company for s in layout.role_sections]
        self.assertEqual(companies, ["Fictional Corp", "Older Fictional Inc"])

    def test_cited_skill_group_ordered_first(self):
        output = TailoredOutput(
            target_company="Fictional Target Co",
            target_role="Fictional Engineer",
            claims=[
                Claim(text="Gofer", source_kind="accomplishment", source_ref="acc-f2"),
            ],
        )
        # acc-f2's own skill is "Gofer", which is in the "languages" group -
        # citing text that mentions "Gofer" should put "languages" first.
        layout = build_layout(output, self.profile)
        self.assertEqual(layout.skill_groups[0][0], "languages")

    def test_projects_included(self):
        output = _valid_output()
        layout = build_layout(output, self.profile)
        self.assertEqual(len(layout.projects), 1)
        title, bullets = layout.projects[0]
        self.assertEqual(title, "Fictional side project")
        self.assertIn("100 fictional users", bullets[0])


class TestRenderResumeCli(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        self.profile_path = self.tmp_path / "profile.yaml"
        self.profile_path.write_text(_FICTIONAL_PROFILE_YAML, encoding="utf-8")

        self.drafts_dir = self.tmp_path / "drafts"
        self.drafts_dir.mkdir()
        self.matches_dir = self.tmp_path / "matches"
        self.matches_dir.mkdir()
        self.out_dir = self.tmp_path / "resumes"

        (self.matches_dir / "2020-01-01.json").write_text(
            '[{"dedupe_key": "fict123", "company": "Fictional Target Co", "title": "Fictional Engineer"}]',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _write_draft(self, output: TailoredOutput) -> Path:
        import json

        path = self.drafts_dir / "fict123.json"
        path.write_text(json.dumps(output.to_dict()), encoding="utf-8")
        return path

    def _run_cli(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pipeline.cli.render_resume",
                "fict123",
                "--draft",
                str(self.drafts_dir / "fict123.json"),
                "--matches-dir",
                str(self.matches_dir),
                "--profile",
                str(self.profile_path),
                "--out-dir",
                str(self.out_dir),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_refuses_unverified_draft(self):
        bad_output = TailoredOutput(
            target_company="Fictional Target Co",
            target_role="Fictional Engineer",
            claims=[
                Claim(text="Did something great", source_kind="accomplishment", source_ref="acc-nonexistent"),
            ],
        )
        self._write_draft(bad_output)

        result = self._run_cli()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("REFUSED", result.stderr)
        self.assertFalse(self.out_dir.exists())

    def test_produces_a_pdf_for_verified_draft(self):
        self._write_draft(_valid_output())

        result = self._run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        canonical = self.out_dir / "fict123.pdf"
        self.assertTrue(canonical.exists())
        self.assertGreater(canonical.stat().st_size, 0)
        with canonical.open("rb") as f:
            header = f.read(5)
        self.assertEqual(header, b"%PDF-")

        friendly_matches = list(self.out_dir.glob("Fictional_Candidate_Resume_*.pdf"))
        self.assertEqual(len(friendly_matches), 1)


if __name__ == "__main__":
    unittest.main()
