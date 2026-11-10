import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_SCRIPT = REPO_ROOT / "scripts" / "check_no_personal_data.sh"


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)


class TestNoPersonalDataGuard(unittest.TestCase):
    def test_passes_on_clean_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _init_repo(tmp_path)
            (tmp_path / "README.md").write_text("hello\n")
            subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

            result = subprocess.run(
                ["bash", str(GUARD_SCRIPT)], cwd=tmp_path, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("OK", result.stdout)

    def test_fails_when_real_profile_is_tracked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _init_repo(tmp_path)
            (tmp_path / "profile").mkdir()
            (tmp_path / "profile" / "profile.yaml").write_text("candidate: {}\n")
            subprocess.run(["git", "add", "-f", "profile/profile.yaml"], cwd=tmp_path, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "oops"], cwd=tmp_path, check=True)

            result = subprocess.run(
                ["bash", str(GUARD_SCRIPT)], cwd=tmp_path, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("profile/profile.yaml", result.stderr)

    def test_fails_when_data_dir_is_tracked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _init_repo(tmp_path)
            (tmp_path / "data").mkdir()
            (tmp_path / "data" / "tracker.xlsx").write_text("fake binary content")
            subprocess.run(["git", "add", "-f", "data/tracker.xlsx"], cwd=tmp_path, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "oops"], cwd=tmp_path, check=True)

            result = subprocess.run(
                ["bash", str(GUARD_SCRIPT)], cwd=tmp_path, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("data/tracker.xlsx", result.stderr)


if __name__ == "__main__":
    unittest.main()
